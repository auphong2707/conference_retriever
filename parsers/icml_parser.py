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
        2025: 259,  # ICML 2025
        2024: 235,  # ICML 2024
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
        Parse ICML papers from HTML (proceedings.mlr.press format)
        
        The website structure has:
        1. Title in a <p class="title"> element
        2. Authors; Proceedings info in a <p class="details"> element
        3. Links [abs][PDF][OpenReview] in a <p class="links"> element
        
        Args:
            soup: BeautifulSoup object
            year: Publication year
        
        Returns:
            List of paper dictionaries
        """
        papers = []
        
        # Find all the link paragraphs (contain [abs] links)
        volume = self.VOLUME_MAP.get(year, '')
        link_paragraphs = soup.find_all('p', class_='links')
        
        for links_p in link_paragraphs:
            try:
                # Find the abs link
                abs_link = links_p.find('a', href=lambda h: h and f'/v{volume}/' in h and h.endswith('.html'))
                if not abs_link:
                    continue
                
                paper_url = abs_link.get('href', '')
                if not paper_url.startswith('http'):
                    paper_url = f"https://proceedings.mlr.press{paper_url}"
                
                # Navigate backwards to find title and authors (they have classes)
                prev = links_p.previous_sibling
                authors_p = None
                title_p = None
                
                # Look for details paragraph (authors)
                while prev:
                    if hasattr(prev, 'name') and prev.name == 'p':
                        if 'details' in prev.get('class', []):
                            authors_p = prev
                            break
                    prev = prev.previous_sibling
                
                # Look for title paragraph
                prev = links_p.previous_sibling
                while prev:
                    if hasattr(prev, 'name') and prev.name == 'p':
                        if 'title' in prev.get('class', []):
                            title_p = prev
                            break
                    prev = prev.previous_sibling
                
                if not title_p:
                    continue
                
                # Extract title
                title = title_p.get_text(strip=True)
                
                # Skip if title seems wrong
                if len(title) < 10:
                    continue
                
                # Extract authors
                authors = []
                if authors_p:
                    authors_text = authors_p.get_text(strip=True)
                    # Format is: "Author1, Author2; Proceedings info; PMLR volume:pages"
                    if ';' in authors_text:
                        authors_part = authors_text.split(';')[0].strip()
                        author_names = [name.strip() for name in authors_part.split(',')]
                        authors = [{"name": name} for name in author_names if name and len(name) > 2]
                
                # Find PDF link
                pdf_link = links_p.find('a', href=lambda h: h and '.pdf' in h)
                pdf_url = pdf_link.get('href') if pdf_link else paper_url.replace('.html', '.pdf')
                
                # Generate paper ID
                paper_id = paper_url.split('/')[-1].replace('.html', '')
                
                # Create paper entry
                paper = {
                    'paper_id': f"icml_{year}_{paper_id}",
                    'title': title,
                    'authors': authors,
                    'conference': 'ICML',
                    'year': year,
                    'url': paper_url,
                    'pdf_url': pdf_url,
                    'venue': f'International Conference on Machine Learning {year}',
                    'source': 'mlr_press'
                }
                
                papers.append(paper)
                
            except Exception as e:
                # Skip malformed entries
                continue
        
        return papers
