"""
DBLP + Semantic Scholar Hybrid Retriever
Retrieves papers from DBLP API and enriches with Semantic Scholar data
"""
import requests
import time
import logging
import os
from typing import List, Dict, Optional
from xml.etree import ElementTree as ET
from datetime import datetime
from fuzzywuzzy import fuzz
from dotenv import load_dotenv

from .base_retriever import BaseRetriever

# Load environment variables
load_dotenv()


logger = logging.getLogger(__name__)


class DBLPHybridRetriever(BaseRetriever):
    """Retriever for conferences using DBLP + Semantic Scholar"""
    
    DBLP_API_BASE = "https://dblp.org/search/publ/api"
    SEMANTIC_SCHOLAR_API_BASE = "https://api.semanticscholar.org/graph/v1"
    
    # DBLP venue mappings for different conferences
    DBLP_VENUES = {
        'icse': 'ICSE',
        'fse': 'SIGSOFT FSE',  # ESEC/FSE or SIGSOFT FSE
        'ase': 'ASE',
        'issta': 'ISSTA',
        'ccs': 'CCS',
        'sp': 'IEEE Symposium on Security and Privacy'
    }
    
    # Alternative venue strings to try
    VENUE_ALTERNATIVES = {
        'fse': ['ESEC/FSE', 'SIGSOFT FSE', 'FSE'],
        'sp': ['IEEE Symposium on Security and Privacy', 'IEEE S&P', 'Oakland']
    }
    
    # Venue filters - exclude workshop/co-located events
    VENUE_EXCLUSIONS = [
        '@',  # Workshop notation (e.g., GE@ICSE, NIER@ICSE)
        'FoSE',  # Future of Software Engineering
        'Workshop',
        'Demo',
        'Poster',
        'Companion',
        'NIER',  # New Ideas track
        'SEIP',  # Software Engineering in Practice
        'SEET',  # Software Engineering Education and Training
        'GE',  # Gender Equality
        'Doctoral',
        'Student',
    ]
    
    def __init__(self, conference_name: str, config: Optional[Dict] = None, enable_semantic_scholar: bool = False, semantic_scholar_api_key: Optional[str] = None):
        """
        Initialize DBLP Hybrid Retriever
        
        Args:
            conference_name: Conference short name
            config: Optional configuration dictionary
            enable_semantic_scholar: Whether to enrich papers with Semantic Scholar data (additional to DBLP's own enrichment)
            semantic_scholar_api_key: Optional API key for Semantic Scholar
        """
        super().__init__(conference_name, enable_semantic_scholar, semantic_scholar_api_key)
        self.config = config or {}
        self.rate_limit = self.config.get('rate_limit', 1.0)
        self.dblp_venue = self.DBLP_VENUES.get(conference_name.lower(), conference_name.upper())
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Research-Paper-Retriever/1.0 (Academic Research; Contact: researcher@example.com)'
        })
        
        # Add Semantic Scholar API key if available
        api_key = semantic_scholar_api_key or os.getenv('SEMANTIC_SCHOLAR_API_KEY')
        if api_key:
            self.session.headers['x-api-key'] = api_key
            logger.info("Using Semantic Scholar API key for higher rate limits")
        else:
            logger.warning("No Semantic Scholar API key found - using limited rate")
        
        self.last_request_time = 0
        self.last_ss_request_time = 0  # Separate timing for Semantic Scholar
        self.fuzzy_threshold = 90  # Minimum similarity score for title matching
        self.semantic_scholar_delay = 1.0 if api_key else 3.0  # With key: 1s, without: 3s
        self.max_retries = 3
        
    def _rate_limit(self):
        """Implement rate limiting"""
        elapsed = time.time() - self.last_request_time
        sleep_time = (1.0 / self.rate_limit) - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def get_papers(self, year: int, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve papers from DBLP and enrich with Semantic Scholar
        
        Args:
            year: Publication year
            limit: Maximum number of papers (None for all)
        
        Returns:
            List of enriched paper dictionaries
        """
        logger.info(f"Retrieving {self.conference_name.upper()} {year} papers from DBLP...")
        
        # Step 1: Get papers from DBLP
        dblp_papers = self._get_dblp_papers(year)
        logger.info(f"Found {len(dblp_papers)} papers in DBLP")
        
        if limit:
            dblp_papers = dblp_papers[:limit]
        
        # Step 2: Enrich with Semantic Scholar (DBLP's built-in enrichment)
        enriched_papers = []
        for i, paper in enumerate(dblp_papers):
            logger.info(f"Enriching paper {i+1}/{len(dblp_papers)}: {paper['title'][:60]}...")
            enriched = self._enrich_with_semantic_scholar(paper)
            enriched_papers.append(enriched)
            
            # Rate limiting between Semantic Scholar requests
            if i < len(dblp_papers) - 1:
                self._rate_limit()
        
        logger.info(f"Successfully retrieved and enriched {len(enriched_papers)} papers")
        return enriched_papers
    
    def _get_dblp_papers(self, year: int) -> List[Dict]:
        """
        Retrieve papers from DBLP API
        
        Args:
            year: Publication year
        
        Returns:
            List of paper dictionaries from DBLP
        """
        all_papers = []
        
        # Try different venue variations
        venues_to_try = [self.dblp_venue]
        if self.conference_name.lower() in self.VENUE_ALTERNATIVES:
            venues_to_try.extend(self.VENUE_ALTERNATIVES[self.conference_name.lower()])
        
        for venue in venues_to_try:
            papers = self._query_dblp_venue(venue, year)
            if papers:
                logger.info(f"Found {len(papers)} papers for venue '{venue}'")
                # Deduplicate based on title
                for paper in papers:
                    if not any(p['title'].lower() == paper['title'].lower() for p in all_papers):
                        all_papers.append(paper)
        
        return all_papers
    
    def _query_dblp_venue(self, venue: str, year: int) -> List[Dict]:
        """
        Query DBLP API for a specific venue and year
        
        Args:
            venue: Venue string
            year: Publication year
        
        Returns:
            List of papers
        """
        papers = []
        first_hit = 0
        max_results = 1000  # DBLP max per request
        
        while True:
            # Build query - use exact venue match
            # For conferences, we want the main proceedings, not workshops
            if self.conference_name.lower() == 'icse':
                query = f'venue:ICSE year:{year}'  
            elif self.conference_name.lower() == 'sp':
                query = f'venue:"IEEE Symposium on Security and Privacy" year:{year}'
            else:
                query = f'venue:{venue} year:{year}'
            
            params = {
                'q': query,
                'format': 'xml',
                'h': max_results,
                'f': first_hit
            }
            
            self._rate_limit()
            
            try:
                response = self.session.get(self.DBLP_API_BASE, params=params, timeout=30)
                response.raise_for_status()
                
                # Parse XML
                root = ET.fromstring(response.content)
                
                # Check total hits
                hits_elem = root.find('.//hits')
                if hits_elem is None:
                    break
                
                total = int(hits_elem.get('total', 0))
                sent = int(hits_elem.get('sent', 0))
                
                if sent == 0:
                    break
                
                # Extract papers
                for hit in root.findall('.//hit'):
                    paper = self._parse_dblp_hit(hit, year)
                    if paper and self._is_main_track(paper):
                        papers.append(paper)
                
                # Check if we've retrieved all papers
                first_hit += sent
                if first_hit >= total:
                    break
                    
            except requests.RequestException as e:
                logger.error(f"DBLP API error: {e}")
                break
            except ET.ParseError as e:
                logger.error(f"XML parsing error: {e}")
                break
        
        return papers
    
    def _parse_dblp_hit(self, hit_element: ET.Element, year: int) -> Optional[Dict]:
        """
        Parse a DBLP hit element into a paper dictionary
        
        Args:
            hit_element: XML element for a paper
            year: Expected publication year
        
        Returns:
            Paper dictionary or None if invalid
        """
        info = hit_element.find('info')
        if info is None:
            return None
        
        # Extract title
        title_elem = info.find('title')
        if title_elem is None or not title_elem.text:
            return None
        title = title_elem.text.strip()
        
        # Extract authors
        authors = []
        for author_elem in info.findall('authors/author'):
            if author_elem.text:
                authors.append({
                    'name': author_elem.text.strip()
                })
        
        # Extract venue
        venue_elem = info.find('venue')
        venue = venue_elem.text.strip() if venue_elem is not None and venue_elem.text else ""
        
        # Extract DOI
        doi_elem = info.find('doi')
        doi = doi_elem.text.strip() if doi_elem is not None and doi_elem.text else None
        
        # Extract URL
        url_elem = info.find('url')
        url = url_elem.text.strip() if url_elem is not None and url_elem.text else None
        
        # Extract year from DBLP (verify it matches)
        year_elem = info.find('year')
        dblp_year = int(year_elem.text) if year_elem is not None and year_elem.text else year
        
        # Create paper entry
        paper = {
            'title': title,
            'authors': authors,
            'year': dblp_year,
            'venue': venue,
            'doi': doi,
            'url': url,
            'source': 'dblp'
        }
        
        return paper
    
    def _is_main_track(self, paper: Dict) -> bool:
        """
        Check if paper is from main conference track (not workshop/co-located)
        
        Args:
            paper: Paper dictionary
        
        Returns:
            True if main track, False if workshop/co-located
        """
        venue = paper.get('venue', '')
        
        # Check if venue contains exclusion keywords
        for exclusion in self.VENUE_EXCLUSIONS:
            if exclusion.lower() in venue.lower():
                logger.debug(f"Excluding paper from '{venue}' (matched: {exclusion})")
                return False
        
        return True
    
    def _enrich_with_semantic_scholar(self, paper: Dict) -> Dict:
        """
        Enrich paper with Semantic Scholar data
        
        Args:
            paper: Paper dictionary from DBLP
        
        Returns:
            Enriched paper dictionary
        """
        # Try to find paper in Semantic Scholar
        ss_data = self._search_semantic_scholar(paper['title'])
        
        if ss_data:
            # Verify title match (fuzzy matching)
            similarity = fuzz.ratio(
                paper['title'].lower(),
                ss_data.get('title', '').lower()
            )
            
            if similarity >= self.fuzzy_threshold:
                # Merge Semantic Scholar data
                paper['abstract'] = ss_data.get('abstract', '')
                paper['citation_count'] = ss_data.get('citationCount', 0)
                paper['reference_count'] = ss_data.get('referenceCount', 0)
                paper['semantic_scholar_id'] = ss_data.get('paperId')
                paper['enriched_by'] = ['semantic_scholar']
                
                # Get PDF URL if available
                if ss_data.get('openAccessPdf'):
                    paper['pdf_url'] = ss_data['openAccessPdf'].get('url')
                
                # Get more detailed author info
                if ss_data.get('authors'):
                    for i, author in enumerate(paper['authors']):
                        if i < len(ss_data['authors']):
                            ss_author = ss_data['authors'][i]
                            author['author_id'] = ss_author.get('authorId')
                
                # Get external IDs
                if ss_data.get('externalIds'):
                    ext_ids = ss_data['externalIds']
                    if 'ArXiv' in ext_ids:
                        paper['arxiv_id'] = ext_ids['ArXiv']
                    if 'DOI' in ext_ids and not paper.get('doi'):
                        paper['doi'] = ext_ids['DOI']
                
                logger.info(f"  [OK] Enriched with Semantic Scholar (match: {similarity}%)")
            else:
                logger.warning(f"  [WARN] Title mismatch (similarity: {similarity}%), skipping enrichment")
                paper['enriched_by'] = []
        else:
            logger.warning(f"  [WARN] Not found in Semantic Scholar")
            paper['enriched_by'] = []
        
        # Generate paper ID
        paper['paper_id'] = self._generate_paper_id(paper)
        
        # Add metadata
        paper['conference'] = self.config.get('short_name', self.conference_name.upper())
        paper['retrieved_at'] = datetime.utcnow().isoformat() + 'Z'
        
        return paper
    
    def _search_semantic_scholar(self, title: str) -> Optional[Dict]:
        """
        Search Semantic Scholar for a paper by title with retry logic
        
        Args:
            title: Paper title
        
        Returns:
            Paper data from Semantic Scholar or None
        """
        # Rate limiting specific to Semantic Scholar
        elapsed = time.time() - self.last_ss_request_time
        sleep_time = self.semantic_scholar_delay - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)
        
        # Use the paper search endpoint
        search_url = f"{self.SEMANTIC_SCHOLAR_API_BASE}/paper/search"
        
        params = {
            'query': title,
            'limit': 1,
            'fields': 'paperId,title,abstract,authors,year,citationCount,referenceCount,openAccessPdf,externalIds,venue'
        }
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(search_url, params=params, timeout=30)
                self.last_ss_request_time = time.time()
                
                if response.status_code == 429:  # Rate limited
                    wait_time = (attempt + 1) * 5  # Exponential backoff: 5, 10, 15 seconds
                    logger.warning(f"Rate limited by Semantic Scholar, waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                
                response.raise_for_status()
                
                data = response.json()
                
                if data.get('data') and len(data['data']) > 0:
                    return data['data'][0]
                
                return None
                
            except requests.RequestException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Semantic Scholar API error (attempt {attempt+1}/{self.max_retries}): {e}")
                    time.sleep(2)
                else:
                    logger.error(f"Semantic Scholar API error after {self.max_retries} attempts: {e}")
            except ValueError as e:
                logger.error(f"JSON parsing error: {e}")
                break
        
        return None
    
    def _generate_paper_id(self, paper: Dict) -> str:
        """
        Generate a unique paper ID
        
        Args:
            paper: Paper dictionary
        
        Returns:
            Unique ID string
        """
        # Use Semantic Scholar ID if available
        if paper.get('semantic_scholar_id'):
            return f"ss_{paper['semantic_scholar_id']}"
        
        # Use DOI if available
        if paper.get('doi'):
            doi_clean = paper['doi'].replace('/', '_').replace('.', '_')
            return f"doi_{doi_clean}"
        
        # Fallback: conference + year + title hash
        import hashlib
        title_hash = hashlib.md5(paper['title'].encode()).hexdigest()[:8]
        return f"{self.conference_name}_{paper['year']}_{title_hash}"
