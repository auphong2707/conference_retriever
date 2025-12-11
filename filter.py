"""
Conference Paper Filter
Filter papers by keywords and remove duplicates
"""
import argparse
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Set, Any
from collections import defaultdict
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PaperFilter:
    """Filter papers based on keywords and deduplication"""
    
    def __init__(self, keyword_groups: Dict[str, List[str]], match_mode: str = 'all'):
        """
        Initialize the paper filter
        
        Args:
            keyword_groups: Dictionary of keyword groups. Each group should have a list of keywords.
                           Papers must match at least one keyword from each group.
            match_mode: 'all' requires matching all groups, 'any' requires matching any group
        """
        self.keyword_groups = keyword_groups
        self.match_mode = match_mode
        
        # Compile regex patterns for each keyword (case-insensitive)
        self.patterns = {}
        for group_name, keywords in keyword_groups.items():
            self.patterns[group_name] = [
                re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
                for keyword in keywords
            ]
    
    def _matches_keyword_group(self, text: str, group_name: str) -> bool:
        """Check if text matches at least one keyword in a group"""
        if not text:
            return False
        
        patterns = self.patterns.get(group_name, [])
        for pattern in patterns:
            if pattern.search(text):
                return True
        return False
    
    def _matches_all_groups(self, text: str) -> bool:
        """Check if text matches at least one keyword from each group"""
        for group_name in self.keyword_groups.keys():
            if not self._matches_keyword_group(text, group_name):
                return False
        return True
    
    def _matches_any_group(self, text: str) -> bool:
        """Check if text matches at least one keyword from any group"""
        for group_name in self.keyword_groups.keys():
            if self._matches_keyword_group(text, group_name):
                return True
        return False
    
    def matches_keywords(self, paper: Dict[str, Any]) -> bool:
        """
        Check if a paper matches the keyword criteria
        
        Args:
            paper: Paper dictionary with 'title' and 'abstract' fields
            
        Returns:
            True if paper matches keyword criteria, False otherwise
        """
        # Combine title and abstract for searching
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        combined_text = f"{title} {abstract}"
        
        if self.match_mode == 'all':
            return self._matches_all_groups(combined_text)
        elif self.match_mode == 'any':
            return self._matches_any_group(combined_text)
        else:
            raise ValueError(f"Invalid match_mode: {self.match_mode}")
    
    def get_paper_key(self, paper: Dict[str, Any]) -> str:
        """
        Generate a unique key for a paper based on title and DOI
        
        Args:
            paper: Paper dictionary
            
        Returns:
            Unique key string
        """
        # Normalize title: lowercase, remove extra whitespace and punctuation
        title = paper.get('title', '').lower().strip()
        title = re.sub(r'[^\w\s]', '', title)
        title = re.sub(r'\s+', ' ', title)
        
        # Use DOI if available, otherwise use normalized title
        doi = paper.get('doi', '')
        if doi:
            return f"doi:{doi}"
        
        # Use Semantic Scholar ID if available
        ss_id = paper.get('semantic_scholar_id', '') or paper.get('paper_id', '')
        if ss_id:
            return f"ss:{ss_id}"
        
        # Fall back to title-based key
        return f"title:{title}"
    
    def deduplicate_papers(self, papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate papers, keeping the most complete version
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            List of deduplicated papers
        """
        seen_keys = {}
        
        for paper in papers:
            key = self.get_paper_key(paper)
            
            if key not in seen_keys:
                seen_keys[key] = paper
            else:
                # Keep the paper with more information
                existing = seen_keys[key]
                
                # Prefer paper with abstract
                if not existing.get('abstract') and paper.get('abstract'):
                    seen_keys[key] = paper
                # Prefer paper with more citations
                elif paper.get('citation_count', 0) > existing.get('citation_count', 0):
                    seen_keys[key] = paper
                # Prefer paper enriched with Semantic Scholar
                elif paper.get('enriched_with_semantic_scholar') and not existing.get('enriched_with_semantic_scholar'):
                    seen_keys[key] = paper
        
        return list(seen_keys.values())
    
    def filter_papers(self, papers: List[Dict[str, Any]], deduplicate: bool = True) -> List[Dict[str, Any]]:
        """
        Filter papers by keywords and optionally deduplicate
        
        Args:
            papers: List of paper dictionaries
            deduplicate: Whether to remove duplicates
            
        Returns:
            List of filtered papers
        """
        # Filter by keywords
        filtered = [paper for paper in papers if self.matches_keywords(paper)]
        
        logger.info(f"Keyword filter: {len(papers)} -> {len(filtered)} papers")
        
        # Deduplicate if requested
        if deduplicate:
            before = len(filtered)
            filtered = self.deduplicate_papers(filtered)
            logger.info(f"Deduplication: {before} -> {len(filtered)} papers")
        
        return filtered


def load_papers_from_directory(directory: Path) -> List[Dict[str, Any]]:
    """
    Load all papers from JSON files in a directory
    
    Args:
        directory: Path to directory containing JSON files
        
    Returns:
        List of all papers from all files
    """
    all_papers = []
    
    json_files = list(directory.glob('*.json'))
    logger.info(f"Found {len(json_files)} JSON files in {directory}")
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                papers = json.load(f)
                if isinstance(papers, list):
                    all_papers.extend(papers)
                    logger.info(f"Loaded {len(papers)} papers from {json_file.name}")
                else:
                    logger.warning(f"Skipping {json_file.name}: not a list")
        except Exception as e:
            logger.error(f"Error loading {json_file.name}: {e}")
    
    logger.info(f"Total papers loaded: {len(all_papers)}")
    return all_papers


def save_papers(papers: List[Dict[str, Any]], output_path: Path, include_stats: bool = True):
    """
    Save filtered papers to JSON file
    
    Args:
        papers: List of paper dictionaries
        output_path: Path to output file
        include_stats: Whether to include statistics in a separate file
    """
    os.makedirs(output_path.parent, exist_ok=True)
    
    # Sort papers by year (descending) and then by title
    papers_sorted = sorted(
        papers,
        key=lambda x: (-x.get('year', 0), x.get('title', ''))
    )
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(papers_sorted, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(papers_sorted)} papers to {output_path}")
    
    # Generate statistics
    if include_stats:
        stats = generate_statistics(papers_sorted)
        stats_path = output_path.parent / f"{output_path.stem}_stats.txt"
        
        with open(stats_path, 'w', encoding='utf-8') as f:
            f.write(stats)
        
        logger.info(f"Saved statistics to {stats_path}")
        print(f"\n{stats}")


def generate_statistics(papers: List[Dict[str, Any]]) -> str:
    """Generate statistics about the filtered papers"""
    stats = []
    stats.append("=" * 60)
    stats.append("FILTERED PAPERS STATISTICS")
    stats.append("=" * 60)
    stats.append(f"Total papers: {len(papers)}")
    stats.append("")
    
    # Papers by year
    papers_by_year = defaultdict(int)
    for paper in papers:
        papers_by_year[paper.get('year', 'Unknown')] += 1
    
    stats.append("Papers by year:")
    for year in sorted(papers_by_year.keys(), reverse=True):
        stats.append(f"  {year}: {papers_by_year[year]}")
    stats.append("")
    
    # Papers by venue
    papers_by_venue = defaultdict(int)
    for paper in papers:
        venue = paper.get('venue') or paper.get('conference', 'Unknown')
        papers_by_venue[venue] += 1
    
    stats.append("Papers by venue:")
    for venue in sorted(papers_by_venue.keys()):
        stats.append(f"  {venue}: {papers_by_venue[venue]}")
    stats.append("")
    
    # Papers with abstracts
    with_abstract = sum(1 for p in papers if p.get('abstract'))
    stats.append(f"Papers with abstracts: {with_abstract} ({with_abstract/len(papers)*100:.1f}%)")
    
    # Papers enriched with Semantic Scholar
    enriched = sum(1 for p in papers if p.get('enriched_with_semantic_scholar'))
    stats.append(f"Papers enriched with Semantic Scholar: {enriched} ({enriched/len(papers)*100:.1f}%)")
    
    stats.append("=" * 60)
    
    return "\n".join(stats)


def main():
    parser = argparse.ArgumentParser(
        description='Filter conference papers by keywords and remove duplicates'
    )
    
    parser.add_argument(
        '--input-dir',
        type=str,
        default='output',
        help='Directory containing JSON files to filter (default: output)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='filtered_papers.json',
        help='Output file path (default: filtered_papers.json)'
    )
    
    parser.add_argument(
        '--keywords',
        type=str,
        nargs='+',
        action='append',
        metavar='GROUP',
        help='Keyword groups (use multiple --keywords for AND logic). Example: --keywords agent --keywords code coding programming --keywords security secure'
    )
    
    parser.add_argument(
        '--no-deduplicate',
        action='store_true',
        help='Disable deduplication'
    )
    
    parser.add_argument(
        '--match-mode',
        choices=['all', 'any'],
        default='all',
        help='Match mode: "all" requires all keyword groups, "any" requires any group (default: all)'
    )
    
    args = parser.parse_args()
    
    # Set up default keywords if none provided
    if not args.keywords:
        keyword_groups = keyword_groups = {
            'agent': [
                # Keep it simple: The entity acting on the code
                'agent', 'agents', 
                'autonomous', 'autonomy', # Defines "Agentic" vs just a model
                'assistant', 'copilot',   # Common academic terms for coding agents
                'bot', 'bots'
            ],
            'coding': [
                # The Domain (Software) + The Action (Fixing)
                'code', 'coding', 
                'program', 'programming', 
                'software', 'repository', 'git',
                # Crucial for "Auto-Fixing":
                'repair', 'patch', 'fix', 'debug' 
            ],
            'security': [
                # The Goal
                'security', 'secure', 
                'vulnerability', 'vulnerabilities', 
                'exploit', 'attack', 
                'bug', 'defect', 'flaw' # "Automated Program Repair" (APR) often targets bugs
            ]
        }
        logger.info("Using default keywords: Agent + Coding + Security")
    else:
        # Convert keyword arguments to dictionary
        keyword_groups = {}
        for i, group in enumerate(args.keywords):
            keyword_groups[f'group_{i+1}'] = group
        logger.info(f"Using custom keyword groups: {keyword_groups}")
    
    # Initialize filter
    paper_filter = PaperFilter(keyword_groups, match_mode=args.match_mode)
    
    # Load papers
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return
    
    papers = load_papers_from_directory(input_dir)
    
    if not papers:
        logger.warning("No papers found to filter")
        return
    
    # Filter papers
    filtered_papers = paper_filter.filter_papers(
        papers,
        deduplicate=not args.no_deduplicate
    )
    
    # Save results
    output_path = Path(args.output)
    save_papers(filtered_papers, output_path)
    
    print(f"\n✓ Filtering complete! Found {len(filtered_papers)} matching papers out of {len(papers)} total.")


if __name__ == '__main__':
    main()
