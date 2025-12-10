"""
Static HTML Retriever
Retrieves papers from conferences with static HTML pages
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from retrievers.base_retriever import BaseRetriever
from utils.rate_limiter import RateLimiter
from utils.cache_manager import CacheManager


class StaticHTMLRetriever(BaseRetriever):
    """Retriever for conferences with static HTML pages"""
    
    def __init__(self, conference_name: str, parser, enable_semantic_scholar: bool = False, semantic_scholar_api_key: Optional[str] = None):
        """
        Initialize static HTML retriever
        
        Args:
            conference_name: Short name of the conference
            parser: Parser instance for the specific conference
            enable_semantic_scholar: Whether to enrich papers with Semantic Scholar data
            semantic_scholar_api_key: Optional API key for Semantic Scholar
        """
        super().__init__(conference_name, enable_semantic_scholar, semantic_scholar_api_key)
        self.parser = parser
        self.rate_limiter = RateLimiter(requests_per_second=1.0)
        self.cache = CacheManager(cache_dir=f"conference_retriever/.cache/{conference_name}")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'ResearchPaperRetriever/1.0 (Educational Purpose)'
        })
    
    def _fetch_html(self, url: str) -> str:
        """
        Fetch HTML content from URL with rate limiting and caching
        
        Args:
            url: URL to fetch
        
        Returns:
            HTML content
        """
        # Check cache first
        cached_html = self.cache.get(url)
        if cached_html:
            return cached_html
        
        # Rate limit
        self.rate_limiter.wait_if_needed()
        
        # Fetch
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            html = response.text
            
            # Cache the result
            self.cache.set(url, html)
            
            return html
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            raise
    
    def get_papers(self, year: int, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve papers from the conference for a given year
        
        Args:
            year: Publication year
            limit: Maximum number of papers to retrieve
        
        Returns:
            List of paper dictionaries
        """
        print(f"Retrieving {self.conference_name.upper()} {year} papers...")
        
        # Get URL for the year
        url = self.parser.get_url(year)
        
        # Fetch HTML
        try:
            html = self._fetch_html(url)
        except Exception as e:
            print(f"Failed to fetch papers for {year}: {e}")
            return []
        
        # Parse HTML
        soup = BeautifulSoup(html, 'lxml')
        papers = self.parser.parse(soup, year)
        
        # Apply limit if specified
        if limit:
            papers = papers[:limit]
        
        print(f"✓ Retrieved {len(papers)} papers from {self.conference_name.upper()} {year}")
        
        return papers
