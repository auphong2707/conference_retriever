# Conference Paper Retriever

A system to retrieve papers from major computer science conferences using different scraping strategies.

## Quick Start

### Installation

```bash
pip install -r semantic_api_approach/requirements.txt
```

### Usage

**Retrieve papers from a conference:**

```bash
# Single year
python retrieve.py neurips --year 2025

# Multiple years
python retrieve.py icml --years 2022-2025

# With limit
python retrieve.py usenix --year 2025 --limit 50
```

**Filter papers by keywords:**

```bash
# Default filter (Agent + Coding + Security)
python filter.py

# Custom output location
python filter.py --output results/filtered_papers.json

# Custom keywords (Agent AND LLM AND Testing)
python filter.py --keywords agent --keywords llm "large language model" --keywords testing test

# Disable deduplication
python filter.py --no-deduplicate

# Match any keyword group instead of all (OR logic)
python filter.py --match-mode any
```

## Supported Conferences

### ✅ Implemented (Static HTML Scraping)
- **NeurIPS** - Conference on Neural Information Processing Systems
- **ICML** - International Conference on Machine Learning  
- **USENIX Security** - USENIX Security Symposium

### 🚧 Planned
- **ICLR** (OpenReview API)
- **ICSE, FSE, ASE, ISSTA** (DBLP + Semantic Scholar)
- **CCS, S&P** (DBLP + Semantic Scholar)

## Features

### Paper Retrieval
- ✅ Static HTML scraping for NeurIPS, ICML, USENIX
- ✅ Rate limiting (1 req/sec)
- ✅ File-based caching (30-day TTL)
- ✅ Year range support
- ✅ JSON output format
- ✅ Standardized paper schema

### Paper Filtering
- ✅ Keyword-based filtering with multiple groups (AND/OR logic)
- ✅ Deduplication based on DOI, Semantic Scholar ID, or title
- ✅ Search in titles and abstracts
- ✅ Automatic statistics generation
- ✅ Keeps most complete version of duplicates
- ✅ Flexible keyword groups (e.g., Agent + Coding + Security)

## Architecture

```
conference_retriever/
├── retrievers/          # Retrieval strategies
│   ├── base_retriever.py
│   └── static_html.py
├── parsers/            # Conference-specific parsers
│   ├── neurips_parser.py
│   ├── icml_parser.py
│   └── usenix_parser.py
├── utils/              # Utilities
│   ├── rate_limiter.py
│   └── cache_manager.py
├── config/             # Configuration
│   ├── conferences.yaml
│   └── settings.yaml
├── output/             # Retrieved papers
├── retrieve.py         # Paper retrieval CLI
└── filter.py          # Paper filtering and deduplication
```

## Implementation Progress

### Phase 1: Foundation ✅
- [x] Directory structure
- [x] Base retriever class
- [x] Rate limiter
- [x] Cache manager
- [x] Configuration system

### Phase 2: Static HTML Scraping ✅
- [x] Static HTML retriever
- [x] NeurIPS parser
- [x] ICML parser
- [x] USENIX Security parser
- [x] CLI interface

### Phase 3: OpenReview API 🚧
- [ ] OpenReview retriever
- [ ] ICLR integration

### Phase 4: DBLP Hybrid 🚧
- [ ] DBLP retriever
- [ ] Semantic Scholar enrichment
- [ ] Title fuzzy matching
- [ ] ICSE, FSE, ASE, ISSTA, CCS, S&P parsers

## Output Format

Papers are saved as JSON with the following schema:

```json
{
  "paper_id": "neurips_2023_123456",
  "title": "Paper Title",
  "authors": [
    {"name": "Author Name"}
  ],
  "conference": "NeurIPS",
  "year": 2023,
  "url": "https://...",
  "pdf_url": "https://...pdf",
  "venue": "Conference on Neural Information Processing Systems",
  "source": "neurips_website"
}
```

## Examples

### Retrieving Papers

```bash
# Get NeurIPS 2023 papers
python retrieve.py neurips --year 2023

# Get ICML papers from 2020-2024
python retrieve.py icml --years 2020-2024

# Get first 10 USENIX Security 2024 papers
python retrieve.py usenix --year 2024 --limit 10

# Custom output path
python retrieve.py neurips --year 2023 --output my_papers.json
```

### Filtering Papers

```bash
# Filter with default keywords (Agent + Coding + Security)
python filter.py --input-dir output --output filtered_papers.json

# Filter for LLM testing papers
python filter.py --keywords llm "language model" --keywords testing test evaluation

# Filter for agent-based papers (any keyword match)
python filter.py --keywords agent --keywords code --keywords security --match-mode any
```

## Paper Filtering System

The `filter.py` script provides powerful filtering capabilities to help you find relevant papers from the retrieved dataset.

### Default Behavior

By default, the filter searches for papers about **Coding Agents and Security**:
- **Agent keywords**: agent, agents
- **Coding keywords**: code, coding, program, programming, software, development
- **Security keywords**: security, secure, vulnerability, vulnerabilities, attack, defense

Papers must match **at least one keyword from EACH group** (AND logic).

### Custom Keyword Groups

Define your own keyword groups for different research topics:

```bash
# Machine Learning + Fairness
python filter.py --keywords "machine learning" "deep learning" --keywords fairness bias "fair ml"

# Blockchain + Smart Contracts
python filter.py --keywords blockchain ethereum --keywords "smart contract" solidity
```

### Deduplication

The filter automatically removes duplicate papers by:
1. First checking for matching DOIs
2. Then checking for matching Semantic Scholar IDs
3. Finally checking for normalized title matches

When duplicates are found, it keeps the version with:
- Abstract (if one has it and the other doesn't)
- More citations
- Semantic Scholar enrichment

Disable deduplication with `--no-deduplicate` if needed.

### Output

The filter generates two files:
- **filtered_papers.json**: The filtered papers, sorted by year (descending) and title
- **filtered_papers_stats.txt**: Statistics including:
  - Total papers found
  - Papers by year
  - Papers by venue/conference
  - Papers with abstracts
  - Semantic Scholar enrichment stats

### Programmatic Usage

See [example_filter_usage.py](example_filter_usage.py) for examples of using the filter programmatically in your own scripts.

## License

Educational/Research Use
