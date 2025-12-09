# Conference Paper Retriever

A system to retrieve papers from major computer science conferences using different scraping strategies.

## Quick Start

### Installation

```bash
pip install -r semantic_api_approach/requirements.txt
```

### Usage

Retrieve papers from a conference:

```bash
# Single year
python main.py neurips --year 2025

# Multiple years
python main.py icml --years 2022-2025

# With limit
python main.py usenix --year 2025 --limit 50
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

- ✅ Static HTML scraping for NeurIPS, ICML, USENIX
- ✅ Rate limiting (1 req/sec)
- ✅ File-based caching (30-day TTL)
- ✅ Year range support
- ✅ JSON output format
- ✅ Standardized paper schema

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
└── main.py            # CLI entry point
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

```bash
# Get NeurIPS 2023 papers
python conference_retriever/main.py neurips --year 2023

# Get ICML papers from 2020-2024
python conference_retriever/main.py icml --years 2020-2024

# Get first 10 USENIX Security 2024 papers
python conference_retriever/main.py usenix --year 2024 --limit 10

# Custom output path
python conference_retriever/main.py neurips --year 2023 --output my_papers.json
```

## License

Educational/Research Use
