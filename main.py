"""
Conference Paper Retriever - Main CLI
Retrieve papers from major computer science conferences
"""
import argparse
import json
import os
import sys
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add the parent directory to the path to enable imports
sys.path.insert(0, str(Path(__file__).parent))

from retrievers.static_html import StaticHTMLRetriever
from retrievers.openreview_api import OpenReviewRetriever
from retrievers.dblp_hybrid import DBLPHybridRetriever
from parsers.neurips_parser import NeurIPSParser
from parsers.icml_parser import ICMLParser
from parsers.usenix_parser import USENIXParser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


PARSERS = {
    'neurips': NeurIPSParser(),
    'icml': ICMLParser(),
    'usenix_security': USENIXParser(),
}


def load_conference_config():
    """Load conference configurations from YAML file"""
    config_path = Path(__file__).parent / 'config' / 'conferences.yaml'
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config['conferences']


def load_settings():
    """Load global settings from YAML file"""
    settings_path = Path(__file__).parent / 'config' / 'settings.yaml'
    with open(settings_path, 'r') as f:
        settings = yaml.safe_load(f)
    return settings


def get_retriever(conference: str, enable_semantic_scholar: bool = False, semantic_scholar_api_key: Optional[str] = None):
    """Get retriever for a conference based on its strategy"""
    configs = load_conference_config()
    
    if conference not in configs:
        available = list(configs.keys())
        raise ValueError(f"Conference '{conference}' not supported. Available: {available}")
    
    config = configs[conference]
    strategy = config.get('strategy', 'static_html')
    
    if strategy == 'static_html':
        if conference not in PARSERS:
            raise ValueError(f"No parser available for {conference}")
        parser = PARSERS[conference]
        return StaticHTMLRetriever(conference, parser, enable_semantic_scholar, semantic_scholar_api_key)
    
    elif strategy == 'openreview':
        return OpenReviewRetriever(conference, config, enable_semantic_scholar, semantic_scholar_api_key)
    
    elif strategy == 'dblp_hybrid':
        return DBLPHybridRetriever(conference, config, enable_semantic_scholar, semantic_scholar_api_key)
    
    else:
        raise ValueError(f"Unknown strategy '{strategy}' for {conference}")


def save_papers(papers, output_path):
    """Save papers to JSON file"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    
    print(f"\nSaved {len(papers)} papers to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Conference Paper Retriever - Retrieve papers from CS conferences'
    )
    
    parser.add_argument(
        'conference',
        choices=['neurips', 'icml', 'usenix_security', 'iclr', 'icse', 'fse', 'ase', 'issta', 'ccs', 'sp'],
        help='Conference to retrieve from'
    )
    
    parser.add_argument(
        '--year',
        type=int,
        help='Specific year to retrieve (e.g., 2023)'
    )
    
    parser.add_argument(
        '--years',
        help='Year range to retrieve (e.g., 2020-2024)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of papers to retrieve per year'
    )
    
    parser.add_argument(
        '--output',
        help='Output file path (default: output/{conference}_{year}.json)'
    )
    
    parser.add_argument(
        '--api-key',
        help='Semantic Scholar API key for higher rate limits (or set SEMANTIC_SCHOLAR_API_KEY env var)'
    )
    
    args = parser.parse_args()
    
    # Determine years to retrieve
    years = []
    if args.years:
        start, end = map(int, args.years.split('-'))
        years = list(range(start, end + 1))
    elif args.year:
        years = [args.year]
    else:
        print("Error: Please specify --year or --years")
        return
    
    # Load settings and configure Semantic Scholar enrichment (enabled by default)
    settings = load_settings()
    enable_semantic_scholar = settings.get('semantic_scholar', {}).get('enabled', True)
    
    # Get API key from args, env, or settings
    api_key = args.api_key or os.getenv('SEMANTIC_SCHOLAR_API_KEY') or settings.get('semantic_scholar', {}).get('api_key')
    
    if enable_semantic_scholar:
        if api_key:
            print("\n🔬 Enriching papers with Semantic Scholar (API key detected - higher rate limits)")
        else:
            print("\n🔬 Enriching papers with Semantic Scholar (limited rate - add API key for faster processing)")
    
    # Get retriever
    try:
        retriever = get_retriever(args.conference, enable_semantic_scholar, api_key)
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Retrieve papers (without enrichment first)
    all_papers = []
    for year in years:
        try:
            papers = retriever.get_papers(year, limit=args.limit)
            all_papers.extend(papers)
        except Exception as e:
            print(f"Error retrieving {args.conference} {year}: {e}")
            continue
    
    if not all_papers:
        print("No papers retrieved")
        return
    
    # Enrich all papers with Semantic Scholar after scraping completes
    if enable_semantic_scholar and retriever.semantic_scholar:
        print(f"\n📚 Scraping complete. Starting enrichment for {len(all_papers)} papers...")
        all_papers = retriever.semantic_scholar.enrich_papers_batch(all_papers, show_progress=True)
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        if len(years) == 1:
            filename = f"{args.conference}_{years[0]}.json"
        else:
            filename = f"{args.conference}_{years[0]}-{years[-1]}.json"
        output_path = os.path.join("output", filename)
    
    # Save results
    save_papers(all_papers, output_path)
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Conference: {args.conference.upper()}")
    print(f"  Years: {', '.join(map(str, years))}")
    print(f"  Total papers: {len(all_papers)}")


if __name__ == '__main__':
    main()
