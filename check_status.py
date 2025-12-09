"""
Quick status check for DBLP batch retrieval
"""
import os
import json
from pathlib import Path

output_dir = Path("output")
conferences = ['icse', 'fse', 'ase', 'issta', 'ccs', 'sp']
years = "2022-2023"

print("DBLP Batch Status Check")
print("=" * 60)

completed = []
in_progress = []

for conf in conferences:
    output_file = output_dir / f"{conf}_{years}.json"
    if output_file.exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        completed.append((conf.upper(), len(papers)))
    else:
        in_progress.append(conf.upper())

if completed:
    print("\nCompleted:")
    for conf, count in completed:
        print(f"  {conf}: {count} papers")

if in_progress:
    print(f"\nIn Progress: {', '.join(in_progress)}")

print(f"\nTotal completed: {len(completed)}/6 conferences")
print("=" * 60)
