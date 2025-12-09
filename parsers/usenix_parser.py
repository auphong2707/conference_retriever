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
        
        # Find all H2 elements that contain presentation links
        # These are paper titles in the technical sessions page
        h2_elements = soup.find_all('h2')
        
        for h2 in h2_elements:
            try:
                # Find the link inside h2
                title_link = h2.find('a', href=lambda x: x and '/presentation/' in str(x))
                
                if not title_link:
                    continue
                
                # Extract title (skip empty titles and non-paper entries)
                title = title_link.get_text(strip=True)
                
                # Skip entries without meaningful titles or known non-paper entries
                if not title or title in ['', 'Show details', 'Hide details'] or \
                   'Proceedings Cover' in title or 'Proceedings Front Matter' in title or \
                   'Errata' in title or 'Attendee List' in title or 'Full Proceedings' in title:
                    continue
                
                # Get paper URL
                paper_url = title_link.get('href', '')
                if paper_url and not paper_url.startswith('http'):
                    paper_url = f"https://www.usenix.org{paper_url}"
                
                # Find the next div.content sibling which contains authors
                authors = []
                content_div = h2.find_next_sibling('div', class_='content')
                
                if content_div:
                    # Get the text content and extract authors
                    # Authors appear at the beginning before "Available Media" or other markers
                    content_text = content_div.get_text()
                    
                    # Authors typically appear before "Available Media" or other keywords
                    author_markers = ['Available Media', 'AVAILABLE MEDIA', 'Video', 'Slides']
                    author_text = content_text
                    
                    for marker in author_markers:
                        if marker in author_text:
                            author_text = author_text.split(marker)[0]
                            break
                    
                    author_text = author_text.strip()
                    
                    if author_text:
                        # Parse authors - typically formatted as:
                        # "Author1, Affiliation; Author2, Affiliation..."
                        # Split by semicolons for multiple authors
                        author_parts = author_text.split(';')
                        
                        for part in author_parts:
                            part = part.strip()
                            if part and len(part) > 2:
                                # Extract just the name (before comma or affiliation)
                                # Sometimes there are commas in affiliations, so we take the first part
                                if ',' in part:
                                    name = part.split(',')[0].strip()
                                else:
                                    name = part.strip()
                                
                                # Additional cleanup: remove " and " at the end
                                if name.endswith(' and'):
                                    name = name[:-4].strip()
                                
                                if name and len(name) > 2:
                                    authors.append({"name": name})
                
                # Look for PDF link in the same section
                pdf_url = None
                # Search in the content div and nearby elements
                section = h2.find_parent(['div', 'section'])
                if section:
                    pdf_link = section.find('a', href=lambda x: x and '.pdf' in str(x).lower())
                    if pdf_link:
                        pdf_url = pdf_link.get('href', '')
                        if pdf_url and not pdf_url.startswith('http'):
                            pdf_url = f"https://www.usenix.org{pdf_url}"
                
                # Create paper ID from URL or title hash
                if '/presentation/' in paper_url:
                    # Extract presentation slug from URL for more stable ID
                    slug = paper_url.split('/presentation/')[-1].strip('/')
                    paper_id = f"usenix_security_{year}_{slug}"
                else:
                    paper_id = f"usenix_security_{year}_{abs(hash(title)) % 1000000}"
                
                paper = {
                    "paper_id": paper_id,
                    "title": title,
                    "authors": authors,
                    "conference": "USENIX Security",
                    "year": year,
                    "url": paper_url,
                    "pdf_url": pdf_url,
                    "venue": "USENIX Security Symposium",
                    "source": "usenix_website"
                }
                
                papers.append(paper)
            
            except Exception as e:
                # Skip malformed entries
                continue
        
        return papers
