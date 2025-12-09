"""
ICML Parser
Parses ICML conference papers from proceedings.mlr.press
"""
from bs4 import BeautifulSoup
from typing import List, Dict


class ICMLParser:
    """Parser for ICML conference website"""
    
    # Volume mapping for ICML years
    VOLUME_MAP = {
        2024: 235,
        2023: 202,
        2022: 162,
        2021: 139,
        2020: 119,
        2019: 97,
        2018: 80,
        2017: 70,
        2016: 48,
        2015: 37,
    }
    
    def get_url(self, year: int) -> str:
        """Get URL for a specific year"""
        volume = self.VOLUME_MAP.get(year)
        if not volume:
            raise ValueError(f"ICML volume not mapped for year {year}")
        return f"https://proceedings.mlr.press/v{volume}/"
    
    def parse(self, soup: BeautifulSoup, year: int) -> List[Dict]:
        """
        Parse ICML papers from HTML
        
        Args:
            soup: BeautifulSoup object
            year: Publication year
        
        Returns:
            List of paper dictionaries
        """
        papers = []
        
        # Find all paper entries
        paper_elements = soup.find_all('div', class_='paper') or \
                        soup.find_all('article') or \
                        soup.find_all('p', class_='title')
        
        for elem in paper_elements:
            try:
                # Extract title
                title_elem = elem.find('p', class_='title') or \
                            elem.find('span', class_='title') or \
                            elem.find('a')
                
                if not title_elem:
                    continue
                
                title_link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if not title_link:
                    continue
                
                title = title_link.get_text(strip=True)
                paper_url = title_link.get('href', '')
                
                # Make absolute URL if relative
                if paper_url and not paper_url.startswith('http'):
                    volume = self.VOLUME_MAP.get(year, '')
                    paper_url = f"https://proceedings.mlr.press/v{volume}/{paper_url}"
                
                # Extract authors
                authors_text = ""
                authors_elem = elem.find('span', class_='authors') or \
                              elem.find('p', class_='details')
                
                if authors_elem:
                    # Get just the authors part
                    authors_text = authors_elem.get_text(strip=True)
                    # Remove "Proceedings of" etc
                    if ';' in authors_text:
                        authors_text = authors_text.split(';')[0]
                
                # Parse authors
                authors = []
                if authors_text:
                    # Split by comma or semicolon
                    author_names = [name.strip() for name in authors_text.replace(';', ',').split(',')]
                    authors = [{"name": name} for name in author_names if name and len(name) > 1]
                
                # Extract PDF link
                pdf_url = ""
                pdf_elem = elem.find('a', class_='pdf') or \
                          elem.find('a', href=lambda x: x and '.pdf' in str(x))
                
                if pdf_elem:
                    pdf_url = pdf_elem.get('href', '')
                    if pdf_url and not pdf_url.startswith('http'):
                        volume = self.VOLUME_MAP.get(year, '')
                        pdf_url = f"https://proceedings.mlr.press/v{volume}/{pdf_url}"
                
                # Create paper ID
                paper_id = f"icml_{year}_{hash(title) % 1000000}"
                
                paper = {
                    "paper_id": paper_id,
                    "title": title,
                    "authors": authors,
                    "conference": "ICML",
                    "year": year,
                    "url": paper_url,
                    "pdf_url": pdf_url if pdf_url else None,
                    "venue": "International Conference on Machine Learning",
                    "source": "icml_website"
                }
                
                papers.append(paper)
            
            except Exception as e:
                # Skip malformed entries
                continue
        
        return papers
