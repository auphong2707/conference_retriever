"""
NeurIPS Parser
Parses NeurIPS conference papers from papers.neurips.cc
"""
from bs4 import BeautifulSoup
from typing import List, Dict


class NeurIPSParser:
    """Parser for NeurIPS conference website"""
    
    def get_url(self, year: int) -> str:
        """Get URL for a specific year"""
        return f"https://papers.neurips.cc/paper/{year}"
    
    def parse(self, soup: BeautifulSoup, year: int) -> List[Dict]:
        """
        Parse NeurIPS papers from HTML
        
        Args:
            soup: BeautifulSoup object
            year: Publication year
        
        Returns:
            List of paper dictionaries
        """
        papers = []
        
        # Find all paper entries with class='conference'
        paper_elements = soup.find_all('li', class_='conference')
        
        for elem in paper_elements:
            try:
                # Extract title and URL
                title_elem = elem.find('a')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                paper_url = title_elem.get('href', '')
                
                # Make absolute URL if relative
                if paper_url and not paper_url.startswith('http'):
                    paper_url = f"https://papers.neurips.cc{paper_url}"
                
                # Extract PDF URL from hash in the paper URL
                # URL format: /paper_files/paper/YEAR/hash/HASH-Abstract-Conference.html
                # PDF format: /paper_files/paper/YEAR/file/HASH-Paper-Conference.pdf
                pdf_url = None
                if '/hash/' in paper_url:
                    try:
                        hash_part = paper_url.split('/hash/')[1].split('-')[0]
                        pdf_url = f"https://papers.neurips.cc/paper_files/paper/{year}/file/{hash_part}-Paper-Conference.pdf"
                    except IndexError:
                        pass
                
                # Extract authors from <i> tag
                authors = []
                authors_elem = elem.find('i')
                if authors_elem:
                    authors_text = authors_elem.get_text(strip=True)
                    # Split by comma and clean up
                    author_names = [name.strip() for name in authors_text.split(',')]
                    authors = [{"name": name} for name in author_names if name]
                
                # Create paper ID from hash
                if '/hash/' in paper_url:
                    try:
                        hash_part = paper_url.split('/hash/')[1].split('-')[0]
                        paper_id = f"neurips_{year}_{hash_part}"
                    except IndexError:
                        paper_id = f"neurips_{year}_{abs(hash(title)) % 1000000}"
                else:
                    paper_id = f"neurips_{year}_{abs(hash(title)) % 1000000}"
                
                paper = {
                    "paper_id": paper_id,
                    "title": title,
                    "authors": authors,
                    "conference": "NeurIPS",
                    "year": year,
                    "url": paper_url,
                    "pdf_url": pdf_url,
                    "venue": "Conference on Neural Information Processing Systems",
                    "source": "neurips_website"
                }
                
                papers.append(paper)
            
            except Exception as e:
                # Skip malformed entries
                continue
        
        return papers
