# Semantic Scholar Integration

## Overview

The Conference Retriever now supports automatic enrichment of paper metadata using the [Semantic Scholar Academic Graph API](https://www.semanticscholar.org/product/api). This feature adds valuable information that may be missing from the original sources, including:

- **Abstract**: Full paper abstract
- **Citation Count**: Number of times the paper has been cited
- **Reference Count**: Number of references in the paper
- **DOI & arXiv ID**: Additional identifiers
- **Semantic Scholar ID & URL**: Direct links to Semantic Scholar
- **Fields of Study**: Academic fields/topics

## Why Add This Feature?

Many conference websites don't provide complete metadata. For example:
- USENIX papers often lack abstracts
- Some conferences don't include citation counts
- Missing DOI or arXiv identifiers

Semantic Scholar's API helps fill these gaps by searching for papers and enriching them with comprehensive metadata.

## Usage

### Command Line

Enable Semantic Scholar enrichment using the `--enrich` flag:

```bash
# Basic usage (limited rate - 100 requests per 5 minutes)
python main.py usenix --year 2022 --enrich

# With API key for higher rate limits (5000 requests per 5 minutes)
python main.py usenix --year 2022 --enrich --api-key YOUR_API_KEY

# Or set environment variable
export SEMANTIC_SCHOLAR_API_KEY=your_api_key_here
python main.py usenix --year 2022 --enrich
```

### Configuration File

You can enable enrichment globally in `config/settings.yaml`:

```yaml
semantic_scholar:
  enabled: true  # Enable by default
  api_key: YOUR_API_KEY  # Optional: Set API key here
```

## Getting an API Key

1. Visit [Semantic Scholar API](https://www.semanticscholar.org/product/api)
2. Click "Get API Key" or "Sign Up"
3. Follow the registration process
4. Copy your API key

**Benefits of API Key:**
- 100 requests/5min → 5000 requests/5min (50x increase)
- More reliable for batch processing
- Better for large-scale data collection

## How It Works

### Matching Process

The enrichment service tries multiple methods to find papers:

1. **DOI Match**: If paper has a DOI, search by DOI (most accurate)
2. **arXiv Match**: If paper has arXiv ID, search by arXiv ID
3. **Title Match**: Search by title and year (with fuzzy matching)

### Title Matching Algorithm

For title-based search:
- Normalizes titles (lowercase, remove punctuation)
- Calculates Jaccard similarity between token sets
- Requires 70% similarity threshold for match
- Year matching provides additional confidence boost

### Rate Limiting

The service respects Semantic Scholar's rate limits:
- **Without API key**: 0.3 requests/second (~100 per 5 min)
- **With API key**: 5 requests/second (~5000 per 5 min)
- Automatic retry with exponential backoff on errors
- Caching prevents redundant API calls

## Output Format

Enriched papers include additional fields:

```json
{
  "paper_id": "usenix_security_2022_lee",
  "title": "Under the Hood of DANE Mismanagement in SMTP",
  "authors": [...],
  "conference": "USENIX Security",
  "year": 2022,
  
  "abstract": "DANE (DNS-based Authentication of Named Entities)...",
  "citation_count": 15,
  "reference_count": 42,
  "doi": "10.1234/example.doi",
  "arxiv_id": "2201.12345",
  "semantic_scholar_id": "abc123def456",
  "semantic_scholar_url": "https://www.semanticscholar.org/paper/...",
  "fields_of_study": ["Computer Science", "Security"],
  "enriched_with_semantic_scholar": true
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `abstract` | string | Full text abstract of the paper |
| `citation_count` | integer | Number of citations (as of retrieval) |
| `reference_count` | integer | Number of papers cited by this paper |
| `doi` | string | Digital Object Identifier |
| `arxiv_id` | string | arXiv preprint identifier |
| `semantic_scholar_id` | string | Unique ID in Semantic Scholar database |
| `semantic_scholar_url` | string | Direct link to paper on Semantic Scholar |
| `fields_of_study` | array | Academic fields/topics |
| `enriched_with_semantic_scholar` | boolean | Whether enrichment was successful |

## Examples

### Example 1: Enrich USENIX Papers

```bash
# Retrieve and enrich USENIX Security 2022 papers
python main.py usenix --year 2022 --enrich

# Output will include abstracts and citation counts
```

### Example 2: Batch Processing Multiple Years

```bash
# Enrich papers from 2022-2025 with API key
python main.py neurips --years 2022-2025 --enrich --api-key YOUR_KEY
```

### Example 3: Check Enrichment Statistics

After running with `--enrich`, check the log output:

```
Enriching with Semantic Scholar: 100%|████████| 150/150
✓ Enriched 142/150 papers with Semantic Scholar data
```

This shows that 142 out of 150 papers were successfully matched and enriched.

## Caching

Results are automatically cached in `.cache/semantic_scholar/`:
- Avoids redundant API calls
- Speeds up re-runs
- Cache persists across sessions
- TTL: 30 days (configurable in settings.yaml)

To clear cache:
```bash
rm -rf conference_retriever/.cache/semantic_scholar/
```

## Troubleshooting

### Low Match Rate

**Problem**: Only 30% of papers enriched

**Solutions**:
- Papers might have non-standard titles
- Papers might be too recent (not yet in Semantic Scholar)
- Try adding DOI or arXiv IDs to your source data first

### Rate Limit Errors

**Problem**: `429 Too Many Requests` errors

**Solutions**:
- Add API key for higher limits
- Reduce number of papers (use `--limit`)
- Wait and retry (cache prevents re-processing)

### Missing Abstracts

**Problem**: Papers found but no abstract

**Explanation**: Some papers in Semantic Scholar don't have abstracts in their database. This is a limitation of the source data, not the integration.

## Best Practices

1. **Use API Key**: Get better rate limits and reliability
2. **Enable Caching**: Keep default cache settings to avoid redundant calls
3. **Batch Processing**: Process papers in reasonable batches (100-500 at a time)
4. **Check Logs**: Monitor enrichment success rate in logs
5. **Validate Results**: Spot-check enriched data for accuracy

## Privacy & Ethics

- This tool uses the public Semantic Scholar API
- Respects rate limits and terms of service
- Only fetches publicly available metadata
- Properly attributes data source in output
- For academic/research purposes only

## API Documentation

Full Semantic Scholar API documentation:
- [API Overview](https://www.semanticscholar.org/product/api)
- [API Documentation](https://api.semanticscholar.org/api-docs/)
- [Terms of Service](https://www.semanticscholar.org/product/api#terms)

## Future Enhancements

Potential improvements for future versions:
- Batch API endpoint support (more efficient)
- Enhanced title matching algorithms
- Support for additional fields (publication venue, influential citations)
- Integration with other academic APIs (CrossRef, OpenAlex)
- Automatic retry and recovery mechanisms
