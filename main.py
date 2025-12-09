"""
Conference Paper Retriever - Main CLI
Retrieve papers from major computer science conferences
"""
import argparse
import json
import os
from datetime import datetime

from retrievers.static_html import StaticHTMLRetriever
from parsers.neurips_parser import NeurIPSParser
from parsers.icml_parser import ICMLParser
from parsers.usenix_parser import USENIXParser


PARSERS = {
    'neurips': NeurIPSParser(),
    'icml': ICMLParser(),
    'usenix': USENIXParser(),
}


def get_retriever(conference: str):
    """Get retriever for a conference"""
    if conference not in PARSERS:
        raise ValueError(f"Conference '{conference}' not supported. Available: {list(PARSERS.keys())}")
    
    parser = PARSERS[conference]
    return StaticHTMLRetriever(conference, parser)


def save_papers(papers, output_path):
    """Save papers to JSON file"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Saved {len(papers)} papers to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Conference Paper Retriever - Retrieve papers from CS conferences'
    )
    
    parser.add_argument(
        'conference',
        choices=['neurips', 'icml', 'usenix'],
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
        help='Output file path (default: conference_retriever/output/{conference}_{year}.json)'
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
    
    # Get retriever
    try:
        retriever = get_retriever(args.conference)
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Retrieve papers
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
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        if len(years) == 1:
            filename = f"{args.conference}_{years[0]}.json"
        else:
            filename = f"{args.conference}_{years[0]}-{years[-1]}.json"
        output_path = os.path.join("conference_retriever", "output", filename)
    
    # Save results
    save_papers(all_papers, output_path)
    
    # Print summary
    print(f"\nSummary:")
    print(f"  Conference: {args.conference.upper()}")
    print(f"  Years: {', '.join(map(str, years))}")
    print(f"  Total papers: {len(all_papers)}")


if __name__ == '__main__':
    main()
