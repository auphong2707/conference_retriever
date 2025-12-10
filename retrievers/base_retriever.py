"""
Base Retriever Class
Abstract base class for all conference retrievers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseRetriever(ABC):
    """Abstract base class for conference paper retrievers"""
    
    def __init__(self, conference_name: str, enable_semantic_scholar: bool = False, semantic_scholar_api_key: Optional[str] = None):
        """
        Initialize the retriever
        
        Args:
            conference_name: Short name of the conference (e.g., 'neurips', 'icml')
            enable_semantic_scholar: Whether to enrich papers with Semantic Scholar data
            semantic_scholar_api_key: Optional API key for Semantic Scholar (higher rate limits)
        """
        self.conference_name = conference_name
        self.papers = []
        self.enable_semantic_scholar = enable_semantic_scholar
        self.semantic_scholar = None
        
        if enable_semantic_scholar:
            from utils.semantic_scholar import SemanticScholarAPI
            self.semantic_scholar = SemanticScholarAPI(api_key=semantic_scholar_api_key)
            logger.info("Semantic Scholar enrichment enabled")
    
    @abstractmethod
    def get_papers(self, year: int, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve papers from the conference for a given year
        
        Args:
            year: Publication year
            limit: Maximum number of papers to retrieve (None for all)
        
        Returns:
            List of paper dictionaries with standardized schema
        """
        pass
    
    def _create_paper_entry(
        self,
        paper_id: str,
        title: str,
        authors: List[Dict],
        year: int,
        **kwargs
    ) -> Dict:
        """
        Create a standardized paper entry
        
        Args:
            paper_id: Unique identifier
            title: Paper title
            authors: List of author dictionaries
            year: Publication year
            **kwargs: Additional optional fields
        
        Returns:
            Standardized paper dictionary
        """
        paper = {
            "paper_id": paper_id,
            "title": title,
            "authors": authors,
            "conference": self.conference_name.upper(),
            "year": year,
            "retrieved_at": datetime.utcnow().isoformat() + "Z",
            "source": f"{self.conference_name}_website"
        }
        
        # Add optional fields if provided
        optional_fields = [
            'abstract', 'pdf_url', 'venue', 'citation_count',
            'reference_count', 'keywords', 'doi', 'arxiv_id', 'url'
        ]
        
        for field in optional_fields:
            if field in kwargs and kwargs[field]:
                paper[field] = kwargs[field]
        
        return paper
    
    def get_papers_multiple_years(self, years: List[int]) -> List[Dict]:
        """
        Retrieve papers from multiple years
        
        Args:
            years: List of years to retrieve
        
        Returns:
            Combined list of papers from all years
        """
        all_papers = []
        for year in years:
            papers = self.get_papers(year)
            all_papers.extend(papers)
        return all_papers
    
    def _enrich_papers_with_semantic_scholar(self, papers: List[Dict]) -> List[Dict]:
        """
        Enrich papers with Semantic Scholar data if enabled
        
        Args:
            papers: List of paper dictionaries
        
        Returns:
            Enriched papers (or original if enrichment disabled)
        """
        if not self.enable_semantic_scholar or not self.semantic_scholar:
            return papers
        
        logger.info(f"Enriching {len(papers)} papers with Semantic Scholar data...")
        return self.semantic_scholar.enrich_papers_batch(papers, show_progress=True)
