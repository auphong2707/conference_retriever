"""
Semantic Scholar API Integration
Enriches paper metadata with abstracts and additional information from Semantic Scholar
"""
import requests
import time
from typing import Dict, Optional, List
from utils.rate_limiter import RateLimiter
from utils.cache_manager import CacheManager
import logging

logger = logging.getLogger(__name__)


class SemanticScholarAPI:
    """Interface to Semantic Scholar API for paper metadata enrichment"""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Semantic Scholar API client
        
        Args:
            api_key: Optional Semantic Scholar API key for higher rate limits
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ResearchPaperRetriever/1.0 (Educational Purpose)'
        })
        
        if api_key:
            self.session.headers.update({
                'x-api-key': api_key
            })
        
        # Rate limiter: 100 req/5min without key, 5000 req/5min with key
        # Be conservative to avoid rate limit issues: ~1 req/sec with key, 1 req/3sec without
        requests_per_second = 1.0 if api_key else 0.33
        self.rate_limiter = RateLimiter(requests_per_second=requests_per_second)
        
        # Cache for API responses
        self.cache = CacheManager(cache_dir="conference_retriever/.cache/semantic_scholar")
    
    def search_paper_by_title(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """
        Search for a paper by title
        
        Args:
            title: Paper title
            year: Publication year (helps with disambiguation)
        
        Returns:
            Paper data from Semantic Scholar or None if not found
        """
        # Check cache
        cache_key = f"search_{title}_{year}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Rate limit
        self.rate_limiter.wait_if_needed()
        
        # Retry logic for network errors
        for attempt in range(3):
            try:
                # Search endpoint
                url = f"{self.BASE_URL}/paper/search"
                params = {
                    'query': title,
                    'fields': 'title,abstract,authors,year,citationCount,referenceCount,publicationTypes,externalIds,url,venue,publicationDate,fieldsOfStudy',
                    'limit': 5  # Get top 5 results for matching
                }
                
                if year:
                    params['year'] = str(year)
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if not data.get('data') or len(data['data']) == 0:
                    logger.info(f"No results found for: {title[:60]}...")
                    self.cache.set(cache_key, None)
                    return None
                
                # Find best match
                best_match = self._find_best_title_match(title, data['data'], year)
                
                if best_match:
                    self.cache.set(cache_key, best_match)
                    logger.info(f"Found match for: {title[:50]}...")
                    return best_match
                
                self.cache.set(cache_key, None)
                return None
                
            except requests.exceptions.Timeout as e:
                if attempt < 2:
                    logger.warning(f"Timeout on attempt {attempt+1}/3 for '{title[:50]}...', retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s
                    continue
                else:
                    logger.warning(f"Timeout after 3 attempts for '{title[:50]}...'")
                    return None
            except requests.exceptions.RequestException as e:
                # For other errors (like connection errors), try once more
                if attempt < 2 and ('Connection' in str(e) or 'Timeout' in str(e)):
                    logger.warning(f"Network error on attempt {attempt+1}/3, retrying...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.warning(f"Error searching Semantic Scholar for '{title[:50]}...': {e}")
                    return None
            except Exception as e:
                logger.error(f"Unexpected error searching Semantic Scholar: {e}")
                return None
        
        # If all retries exhausted
        return None
    
    def get_paper_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Get paper by DOI
        
        Args:
            doi: Digital Object Identifier
        
        Returns:
            Paper data from Semantic Scholar or None if not found
        """
        cache_key = f"doi_{doi}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        self.rate_limiter.wait_if_needed()
        
        for attempt in range(3):
            try:
                url = f"{self.BASE_URL}/paper/DOI:{doi}"
                params = {
                    'fields': 'title,abstract,authors,year,citationCount,referenceCount,publicationTypes,externalIds,url,venue,publicationDate,fieldsOfStudy'
                }
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                self.cache.set(cache_key, data)
                return data
                
            except requests.exceptions.Timeout:
                if attempt < 2:
                    logger.warning(f"Timeout on attempt {attempt+1}/3 for DOI {doi}, retrying...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.warning(f"Timeout after 3 attempts for DOI {doi}")
                    self.cache.set(cache_key, None)
                    return None
            except requests.exceptions.RequestException as e:
                if attempt < 2 and ('Connection' in str(e) or 'Timeout' in str(e)):
                    logger.warning(f"Network error on attempt {attempt+1}/3, retrying...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.warning(f"Error fetching DOI {doi} from Semantic Scholar: {e}")
                    self.cache.set(cache_key, None)
                    return None
    
    def get_paper_by_arxiv_id(self, arxiv_id: str) -> Optional[Dict]:
        """
        Get paper by arXiv ID
        
        Args:
            arxiv_id: arXiv identifier
        
        Returns:
            Paper data from Semantic Scholar or None if not found
        """
        cache_key = f"arxiv_{arxiv_id}"
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        self.rate_limiter.wait_if_needed()
        
        for attempt in range(3):
            try:
                url = f"{self.BASE_URL}/paper/ARXIV:{arxiv_id}"
                params = {
                    'fields': 'title,abstract,authors,year,citationCount,referenceCount,publicationTypes,externalIds,url,venue,publicationDate,fieldsOfStudy'
                }
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                self.cache.set(cache_key, data)
                return data
                
            except requests.exceptions.Timeout:
                if attempt < 2:
                    logger.warning(f"Timeout on attempt {attempt+1}/3 for arXiv {arxiv_id}, retrying...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.warning(f"Timeout after 3 attempts for arXiv {arxiv_id}")
                    self.cache.set(cache_key, None)
                    return None
            except requests.exceptions.RequestException as e:
                if attempt < 2 and ('Connection' in str(e) or 'Timeout' in str(e)):
                    logger.warning(f"Network error on attempt {attempt+1}/3, retrying...")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.warning(f"Error fetching arXiv {arxiv_id} from Semantic Scholar: {e}")
                    self.cache.set(cache_key, None)
                    return None
    
    def _find_best_title_match(self, query_title: str, candidates: List[Dict], year: Optional[int] = None) -> Optional[Dict]:
        """
        Find the best matching paper from search results
        
        Args:
            query_title: The original title we're searching for
            candidates: List of candidate papers from API
            year: Expected publication year
        
        Returns:
            Best matching paper or None
        """
        if not candidates:
            return None
        
        # Normalize title for comparison
        query_normalized = self._normalize_title(query_title)
        
        best_match = None
        best_score = 0
        
        for candidate in candidates:
            candidate_title = candidate.get('title', '')
            candidate_normalized = self._normalize_title(candidate_title)
            
            # Calculate similarity score
            score = self._title_similarity(query_normalized, candidate_normalized)
            
            # Boost score if year matches
            if year and candidate.get('year') == year:
                score += 0.2
            
            if score > best_score and score > 0.7:  # Threshold for accepting match
                best_score = score
                best_match = candidate
        
        return best_match
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        import re
        # Convert to lowercase
        title = title.lower()
        # Remove punctuation and extra spaces
        title = re.sub(r'[^\w\s]', ' ', title)
        title = re.sub(r'\s+', ' ', title)
        return title.strip()
    
    def _title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity between two titles using token overlap
        
        Returns:
            Similarity score between 0 and 1
        """
        tokens1 = set(title1.split())
        tokens2 = set(title2.split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        # Jaccard similarity
        jaccard = len(intersection) / len(union) if union else 0
        
        # Also check if one is substring of other (for cases with extra subtitles)
        substring_match = 0
        if title1 in title2 or title2 in title1:
            substring_match = 0.3
        
        return min(jaccard + substring_match, 1.0)
    
    def enrich_paper(self, paper: Dict) -> Dict:
        """
        Enrich a paper dictionary with Semantic Scholar data
        
        Args:
            paper: Paper dictionary with at minimum 'title' and 'year'
        
        Returns:
            Enriched paper dictionary
        """
        # Track if we made an API call (not from cache)
        made_api_call = False
        
        # Try different methods to find the paper
        ss_data = None
        
        # 1. Try DOI if available
        if paper.get('doi') and not ss_data:
            ss_data = self.get_paper_by_doi(paper['doi'])
            if ss_data:
                made_api_call = True
        
        # 2. Try arXiv ID if available
        if paper.get('arxiv_id') and not ss_data:
            ss_data = self.get_paper_by_arxiv_id(paper['arxiv_id'])
            if ss_data:
                made_api_call = True
        
        # 3. Try title search
        if not ss_data:
            ss_data = self.search_paper_by_title(
                paper.get('title', ''),
                paper.get('year')
            )
            if ss_data:
                made_api_call = True
        
        # Enrich paper with Semantic Scholar data
        if ss_data:
            # Add abstract if not present
            if 'abstract' not in paper or not paper['abstract']:
                paper['abstract'] = ss_data.get('abstract')
            
            # Add citation count
            if ss_data.get('citationCount') is not None:
                paper['citation_count'] = ss_data['citationCount']
            
            # Add reference count
            if ss_data.get('referenceCount') is not None:
                paper['reference_count'] = ss_data['referenceCount']
            
            # Add external IDs if not present
            if ss_data.get('externalIds'):
                ext_ids = ss_data['externalIds']
                if 'doi' not in paper and ext_ids.get('DOI'):
                    paper['doi'] = ext_ids['DOI']
                if 'arxiv_id' not in paper and ext_ids.get('ArXiv'):
                    paper['arxiv_id'] = ext_ids['ArXiv']
            
            # Add Semantic Scholar ID
            if ss_data.get('paperId'):
                paper['semantic_scholar_id'] = ss_data['paperId']
            
            # Add Semantic Scholar URL
            if ss_data.get('url'):
                paper['semantic_scholar_url'] = ss_data['url']
            
            # Add fields of study
            if ss_data.get('fieldsOfStudy'):
                paper['fields_of_study'] = ss_data['fieldsOfStudy']
            
            # Mark as enriched
            paper['enriched_with_semantic_scholar'] = True
            
            logger.info(f"✓ Enriched: {paper['title'][:60]}...")
        else:
            paper['enriched_with_semantic_scholar'] = False
            logger.info(f"✗ Not found: {paper['title'][:60]}...")
        
        return paper
    
    def enrich_papers_batch(self, papers: List[Dict], show_progress: bool = True) -> List[Dict]:
        """
        Enrich a batch of papers with Semantic Scholar data
        
        Args:
            papers: List of paper dictionaries
            show_progress: Whether to show progress bar
        
        Returns:
            List of enriched paper dictionaries
        """
        enriched_papers = []
        
        if show_progress:
            try:
                from tqdm import tqdm
                papers_iter = tqdm(papers, desc="Enriching with Semantic Scholar")
            except ImportError:
                papers_iter = papers
        else:
            papers_iter = papers
        
        for i, paper in enumerate(papers_iter):
            # Log progress every 10 papers
            if i > 0 and i % 10 == 0:
                enriched_so_far = sum(1 for p in enriched_papers if p.get('enriched_with_semantic_scholar'))
                logger.info(f"Progress: {i}/{len(papers)} papers processed, {enriched_so_far} enriched")
            
            enriched_paper = self.enrich_paper(paper)
            enriched_papers.append(enriched_paper)
            
            # Enforce minimum delay between papers to be safe with rate limits
            # Increase delay to be more conservative (1 second minimum)
            if i < len(papers) - 1:
                time.sleep(1.0)  # 1 full second between each paper
        
        # Log statistics
        enriched_count = sum(1 for p in enriched_papers if p.get('enriched_with_semantic_scholar'))
        logger.info(f"Enriched {enriched_count}/{len(papers)} papers with Semantic Scholar data")
        
        return enriched_papers
