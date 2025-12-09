"""
USENIX Security Parser
Parses USENIX Security Symposium papers from usenix.org
"""
from bs4 import BeautifulSoup
from typing import List, Dict


class USENIXParser:
    """Parser for USENIX Security Symposium website"""
    
    def get_url(self, year: int) -> str:
        """Get URL for a specific year"""
        year_short = str(year)[2:]  # Get last 2 digits
        return f"https://www.usenix.org/conference/usenixsecurity{year_short}/technical-sessions"
    
    def parse(self, soup: BeautifulSoup, year: int) -> List[Dict]:
        """
        Parse USENIX Security papers from HTML
        
        Args:
            soup: BeautifulSoup object
            year: Publication year
        
        Returns:
            List of paper dictionaries
        """
        papers = []
        
        # Find all paper entries (USENIX uses views-row for session entries)
        paper_elements = soup.find_all('div', class_='views-row') or \
                        soup.find_all('article', class_='node')
        
        for elem in paper_elements:
            try:
                # Extract title
                title_elem = elem.find('h3', class_='node-title') or \
                            elem.find('h2', class_='node-title') or \
                            elem.find('a', class_='node-title')
                
                if not title_elem:
                    title_elem = elem.find('a')
                
                if not title_elem:
                    continue
                
                title_link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if not title_link:
                    continue
                
                title = title_link.get_text(strip=True)
                paper_url = title_link.get('href', '')
                
                # Make absolute URL if relative
                if paper_url and not paper_url.startswith('http'):
                    paper_url = f"https://www.usenix.org{paper_url}"
                
                # Extract authors/presenters
                authors_text = ""
                authors_elem = elem.find('div', class_='field-name-field-presenters') or \
                              elem.find('div', class_='field-name-field-paper-people-names') or \
                              elem.find('span', class_='presenters')
                
                if authors_elem:
                    authors_text = authors_elem.get_text(strip=True)
                
                # Parse authors
                authors = []
                if authors_text:
                    # Remove labels like "Presenter:" or "Authors:"
                    authors_text = authors_text.replace('Presenter:', '').replace('Authors:', '').strip()
                    # Split by common delimiters
                    author_names = [name.strip() for name in authors_text.replace(';', ',').split(',')]
                    authors = [{"name": name} for name in author_names if name and len(name) > 2]
                
                # Extract abstract
                abstract = ""
                abstract_elem = elem.find('div', class_='field-name-body') or \
                               elem.find('div', class_='abstract')
                
                if abstract_elem:
                    abstract = abstract_elem.get_text(strip=True)
                
                # Extract PDF link
                pdf_url = ""
                pdf_elem = elem.find('a', href=lambda x: x and '.pdf' in str(x))
                if pdf_elem:
                    pdf_url = pdf_elem.get('href', '')
                    if pdf_url and not pdf_url.startswith('http'):
                        pdf_url = f"https://www.usenix.org{pdf_url}"
                
                # Create paper ID
                paper_id = f"usenix_security_{year}_{hash(title) % 1000000}"
                
                paper = {
                    "paper_id": paper_id,
                    "title": title,
                    "authors": authors,
                    "conference": "USENIX Security",
                    "year": year,
                    "url": paper_url,
                    "pdf_url": pdf_url if pdf_url else None,
                    "abstract": abstract if abstract else None,
                    "venue": "USENIX Security Symposium",
                    "source": "usenix_website"
                }
                
                papers.append(paper)
            
            except Exception as e:
                # Skip malformed entries
                continue
        
        return papers
