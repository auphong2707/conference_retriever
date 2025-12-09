"""
Batch retrieve all DBLP conferences for 2022-2023
This will take several hours but ensures exhaustive coverage
"""
import sys
from pathlib import Path
import json
import yaml
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from retrievers.dblp_hybrid import DBLPHybridRetriever

# Load conference configs
with open('config/conferences.yaml', 'r') as f:
    configs = yaml.safe_load(f)['conferences']

# Conferences and years to retrieve
dblp_conferences = ['icse', 'fse', 'ase', 'issta', 'ccs', 'sp']
years = [2022, 2023]

print("=" * 80)
print("DBLP Batch Retrieval - All Software Engineering & Security Conferences")
print("=" * 80)
print(f"Conferences: {', '.join([c.upper() for c in dblp_conferences])}")
print(f"Years: {', '.join(map(str, years))}")
print("=" * 80)
print()

total_papers = 0
all_results = {}

for conf in dblp_conferences:
    conf_papers = []
    config = configs[conf]
    
    print(f"\n{'='*80}")
    print(f"Processing {config['short_name']} ({conf.upper()})")
    print(f"{'='*80}\n")
    
    retriever = DBLPHybridRetriever(conf, config)
    
    for year in years:
        try:
            print(f"Retrieving {conf.upper()} {year}...")
            start_time = datetime.now()
            
            papers = retriever.get_papers(year=year)
            
            elapsed = (datetime.now() - start_time).total_seconds()
            print(f"[OK] Retrieved {len(papers)} papers in {elapsed:.1f}s")
            print()
            
            conf_papers.extend(papers)
            
        except Exception as e:
            print(f"[X] Error retrieving {conf.upper()} {year}: {e}")
            print()
    
    # Save conference results
    if conf_papers:
        output_file = f"output/{conf}_{years[0]}-{years[-1]}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(conf_papers, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Saved {len(conf_papers)} papers to {output_file}")
        total_papers += len(conf_papers)
        
        all_results[conf] = {
            'papers': len(conf_papers),
            'years': years,
            'output_file': output_file
        }

print("\n" + "=" * 80)
print("BATCH RETRIEVAL COMPLETE")
print("=" * 80)
print(f"\nTotal papers retrieved: {total_papers}")
print("\nBreakdown by conference:")
for conf, result in all_results.items():
    print(f"  {conf.upper()}: {result['papers']} papers")

# Save summary
summary = {
    'retrieval_date': datetime.now().isoformat(),
    'total_papers': total_papers,
    'conferences': all_results
}

with open('output/dblp_batch_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print(f"\nSaved summary to output/dblp_batch_summary.json")
