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
        
        # Find all paper entries
        paper_elements = soup.find_all('li', class_=lambda x: x and 'paper' in x.lower()) or \
                        soup.find_all('div', class_=lambda x: x and 'paper' in x.lower())
        
        if not paper_elements:
            # Try alternative structure
            paper_elements = soup.find_all('li')
        
        for elem in paper_elements:
            try:
                # Extract title
                title_elem = elem.find('a', href=lambda x: x and '/paper/' in x)
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                paper_url = title_elem.get('href', '')
                
                # Make absolute URL if relative
                if paper_url and not paper_url.startswith('http'):
                    paper_url = f"https://papers.neurips.cc{paper_url}"
                
                # Extract authors
                authors_text = ""
                authors_elem = elem.find('i') or elem.find('span', class_='authors')
                if authors_elem:
                    authors_text = authors_elem.get_text(strip=True)
                
                # Parse authors
                authors = []
                if authors_text:
                    author_names = [name.strip() for name in authors_text.split(',')]
                    authors = [{"name": name} for name in author_names if name]
                
                # Extract PDF link
                pdf_url = ""
                pdf_elem = elem.find('a', href=lambda x: x and '.pdf' in str(x))
                if pdf_elem:
                    pdf_url = pdf_elem.get('href', '')
                    if pdf_url and not pdf_url.startswith('http'):
                        pdf_url = f"https://papers.neurips.cc{pdf_url}"
                
                # Create paper ID
                paper_id = f"neurips_{year}_{hash(title) % 1000000}"
                
                paper = {
                    "paper_id": paper_id,
                    "title": title,
                    "authors": authors,
                    "conference": "NeurIPS",
                    "year": year,
                    "url": paper_url,
                    "pdf_url": pdf_url if pdf_url else None,
                    "venue": "Conference on Neural Information Processing Systems",
                    "source": "neurips_website"
                }
                
                papers.append(paper)
            
            except Exception as e:
                # Skip malformed entries
                continue
        
        return papers
