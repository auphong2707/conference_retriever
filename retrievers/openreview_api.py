"""
OpenReview API Retriever
Strategy for retrieving papers from conferences that use OpenReview (e.g., ICLR)
"""

import openreview
from typing import List, Dict, Optional
import logging
from datetime import datetime
import time

from .base_retriever import BaseRetriever

logger = logging.getLogger(__name__)


class OpenReviewRetriever(BaseRetriever):
    """Retriever for conferences using OpenReview API"""
    
    def __init__(self, conference_key: str, config: Dict):
        super().__init__(conference_key)
        self.config = config
        self.conference_name = config.get('short_name', conference_key)
        self.rate_limit = config.get('rate_limit', 0.5)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenReview client"""
        try:
            # Use API v1 which has better data availability for historical conferences
            self.client = openreview.Client(
                baseurl='https://api.openreview.net',
                username=None,  # Optional: can be added from env
                password=None   # Optional: can be added from env
            )
            logger.info("OpenReview API v1 client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenReview client: {e}")
            raise
    
    def get_papers(self, year: int, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve papers from OpenReview for a specific year
        
        Args:
            year: Year to retrieve papers for
            limit: Maximum number of papers to retrieve (None for all)
            
        Returns:
            List of paper dictionaries
        """
        papers = self.retrieve_papers(year)
        
        if limit:
            papers = papers[:limit]
        
        return papers
    
    def retrieve_papers(self, year: int) -> List[Dict]:
        """
        Retrieve papers from OpenReview for a specific year
        
        Args:
            year: Year to retrieve papers for
            
        Returns:
            List of paper dictionaries
        """
        if year not in self.config.get('years_available', []):
            logger.warning(f"Year {year} not available for {self.conference_name}")
            return []
        
        logger.info(f"Retrieving papers from OpenReview: {self.conference_name} {year}")
        
        try:
            # Get accepted papers by checking the invitation and filtering by venue
            accepted_papers = self._get_accepted_by_invitation(year)
            logger.info(f"Found {len(accepted_papers)} accepted papers")
            
            # Parse papers into standard format
            papers = []
            for submission in accepted_papers:
                try:
                    paper = self._parse_submission(submission, year)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    logger.error(f"Error parsing submission {submission.id}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(papers)} papers")
            return papers
            
        except Exception as e:
            logger.error(f"Error retrieving papers from OpenReview: {e}")
            return []
    
    def _get_accepted_by_invitation(self, year: int) -> List:
        """
        Get all submissions for an invitation and filter for accepted
        
        Args:
            year: Conference year
            
        Returns:
            List of accepted submission notes
        """
        invitations = self.config.get('openreview_invitations', {})
        invitation = invitations.get(year)
        
        if not invitation:
            logger.error(f"No invitation found for year {year}")
            return []
        
        accepted_papers = []
        
        try:
            logger.info(f"Fetching submissions from invitation: {invitation}")
            
            # API v1 uses get_notes with offset/limit pagination
            offset = 0
            limit = 1000
            total_count = 0
            
            while True:
                batch = self.client.get_notes(
                    invitation=invitation,
                    limit=limit,
                    offset=offset
                )
                
                if not batch:
                    break
                
                total_count += len(batch)
                
                # Filter for accepted papers
                for note in batch:
                    # In API v1, venue is in content
                    venue = note.content.get('venue', '')
                    
                    # Check if paper was accepted based on venue
                    # Accepted papers have venue like "ICLR 2023 poster", "ICLR 2023 oral", "ICLR 2023 spotlight"
                    # Rejected/withdrawn have "Submitted to ICLR 2023" or similar
                    if self._is_accepted_venue(venue, year):
                        accepted_papers.append(note)
                        logger.debug(f"Found accepted paper: {note.id} - {venue}")
                
                logger.info(f"Processed {total_count} submissions, found {len(accepted_papers)} accepted")
                
                # If we got fewer than limit, we're done
                if len(batch) < limit:
                    break
                
                offset += limit
                time.sleep(1.0 / self.rate_limit)
            
            logger.info(f"Total processed: {total_count} submissions")
            logger.info(f"Found {len(accepted_papers)} accepted papers")
            return accepted_papers
            
        except Exception as e:
            logger.error(f"Error fetching submissions: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _is_accepted_venue(self, venue: str, year: int) -> bool:
        """
        Check if a venue string indicates an accepted paper
        
        Args:
            venue: Venue string from paper
            year: Conference year
            
        Returns:
            True if accepted, False otherwise
        """
        if not venue:
            return False
        
        venue_lower = venue.lower()
        year_str = str(year)
        
        # Accepted papers have venue like "ICLR 2023 poster/oral/spotlight/notable"
        # Rejected have "Submitted to ICLR 2023" or "Withdrawn Submission"
        if year_str in venue and 'iclr' in venue_lower:
            # Exclude submission-only or withdrawn
            if 'submitted' in venue_lower or 'withdrawn' in venue_lower:
                return False
            # Accept if has presentation type (poster, oral, spotlight, notable)
            if any(pres in venue_lower for pres in ['poster', 'oral', 'spotlight', 'notable', 'conference']):
                return True
        
        return False
    
    def _parse_submission(self, submission, year: int) -> Optional[Dict]:
        """
        Parse OpenReview submission into standard paper format
        
        Args:
            submission: OpenReview note object (API v1)
            year: Conference year
            
        Returns:
            Parsed paper dictionary or None if parsing fails
        """
        try:
            content = submission.content
            
            # Extract title (in API v1, it's directly a string)
            title = content.get('title', '')
            
            # Extract authors
            authors_data = content.get('authors', [])
            authors = []
            for author in authors_data:
                if isinstance(author, str):
                    authors.append({
                        'name': author,
                        'affiliation': None
                    })
                elif isinstance(author, dict):
                    authors.append({
                        'name': author.get('name', ''),
                        'affiliation': author.get('affiliation', None)
                    })
            
            # Extract abstract
            abstract = content.get('abstract', '')
            
            # Extract keywords
            keywords = content.get('keywords', [])
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split(',')]
            
            # Get PDF URL
            pdf_url = content.get('pdf', None)
            if pdf_url and not pdf_url.startswith('http'):
                pdf_url = f"https://openreview.net{pdf_url}"
            
            # Get forum URL (main discussion page)
            forum_id = submission.forum if hasattr(submission, 'forum') else submission.id
            url = f"https://openreview.net/forum?id={forum_id}"
            
            # Get venue information
            venue = content.get('venue', '')
            
            # Create paper dictionary
            paper = {
                'paper_id': f"openreview_{submission.id}",
                'title': title,
                'authors': authors,
                'conference': self.config['short_name'],
                'year': year,
                'abstract': abstract if abstract else None,
                'pdf_url': pdf_url,
                'url': url,
                'venue': venue if venue else f"{self.config['name']} {year}",
                'keywords': keywords if keywords else None,
                'retrieved_at': datetime.now().isoformat(),
                'source': 'openreview',
                'metadata': {
                    'openreview_id': submission.id,
                    'forum_id': forum_id,
                    'invitation': submission.invitation if hasattr(submission, 'invitation') else None
                }
            }
            
            return paper
            
        except Exception as e:
            logger.error(f"Error parsing submission: {e}")
            import traceback
            traceback.print_exc()
            return None
