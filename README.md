# bdjobs-scraper

**DISCLAIMER:** This is for educational and research purposes only.

A scraper for BDJobs.com that uses their REST API to collect comprehensive job market data from Bangladesh. The scraper extracts 31+ fields per job including salary, requirements, company info, and more.

## How We Found The API

The BDJobs website underwent a major overhaul, migrating from server-side rendered pages to an Angular SPA. This initially broke our HTML-based scraper, but led us to discover a much better solution.

### Discovery Process

1. **Initial Problem**: The website changed to use JavaScript-rendered pages, making traditional HTML scraping impossible
2. **Network Analysis**: Used browser DevTools (Network tab) to inspect XHR/Fetch requests
3. **Found Two Key Endpoints**:
   
   **List API** - Returns paginated job listings:
   ```
   https://gateway.bdjobs.com/recruitment-account-test/api/JobSearch/GetJobSearch?isPro=1&rpp=50&pg=X
   ```
   - `isPro=1` returns ALL jobs (regular + premium + early access)
   - `rpp=50` sets results per page
   - `pg=X` is the page number
   - Returns ~60 jobs per page (50 regular + 10 premium)

   **Details API** - Returns complete job information:
   ```
   https://gateway.bdjobs.com/ActtivejobsTest/api/JobSubsystem/jobDetails?jobId=X
   ```
   - Returns 31+ structured fields per job
   - Much cleaner than parsing HTML
   - No CSS class dependencies

4. **Key Insights**:
   - The API has no authentication requirements
   - Rate limiting is lenient (we use 0.25s between list pages, no delay for details)
   - Response format is consistent JSON
   - Some fields contain HTML (we strip tags with BeautifulSoup)

### Why This Is Better Than HTML Scraping

| HTML Scraping (Old) | API Scraping (New) |
|--------------------|--------------------|
| Brittle CSS selectors(XPath is too complicated) | Structured JSON |
| Breaks with layout changes | Stable API contract |
| Incomplete data | 31+ comprehensive fields |
| Slow parsing | Fast JSON parsing |
| Complex error handling | Simple HTTP status codes |

## Architecture

### Current Implementation

```
┌─────────────────┐
│   List API      │  Fetch all job IDs
│   (110 pages)   │  0.25s delay between pages
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ~5,500 Job IDs │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Details API    │  Batch processing (20 at a time)
│  (per job)      │  No delay, connection pool limited
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Dynamic CSV    │  Automatically adds new columns
│  31+ fields     │  UTF-8 encoded
└─────────────────┘
```

### Features

- **Dynamic CSV Columns**: Automatically detects and adds new API fields
- **Concurrent Requests**: Processes jobs in parallel batches of 20
- **Connection Pooling**: Max 5 concurrent connections to prevent overwhelming the API
- **Retry Mechanism**: Up to 10 automatic retries for failed requests
- **HTML Stripping**: Cleans HTML tags from API responses for readable CSV output
- **Progress Tracking**: Real-time feedback during scraping
- **Memory Efficient**: Processes jobs in batches, doesn't load all data at once

### Data Extracted (31+ fields)

- Job info: ID, title, nature (full-time/part-time), workplace, context
- Company: name, business, address, website, logo
- Requirements: education, experience, skills, age, gender, additional requirements
- Compensation: salary range, min/max salary, other benefits
- Application: deadlines, instructions, online apply option, email/URL
- Location: job location
- Dates: posted date, deadline

## Usage

## Installation

```bash
# Clone the repo
git clone <repo-url>
cd bdjobs-scraper

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```
### Full Scrape

Scrapes all ~5,500 jobs (takes ~20-30 minutes):

```bash
python scraper/bdjobs.py
```

Output: `dataset/bdjobs-{timestamp}.csv`

### Test with Small Sample

Edit `test_quick.py` to configure:

```python
TEST_PAGES = 1        # Number of pages to fetch (50 jobs/page)
TEST_JOBS_LIMIT = 5   # Max jobs to process (or None for all)
```

Then run:

```bash
python test_quick.py
```

Output: `dataset/bdjobs-test-{timestamp}.csv`

### Run Tests

```bash
PYTHONPATH=. python tests/test.py
```


## Performance

- **List API**: ~110 pages × 0.25s = ~28 seconds
- **Details API**: ~5,500 jobs in batches of 20 = ~5-8 minutes
- **Total Time**: ~10 minutes for complete dataset
- **Output Size**: ~13MB CSV with all jobs

## Technical Notes

### Rate Limiting Strategy

We experimented with different rate limits and found:
- List API: 0.25s delay is safe and fast
- Details API: No delay needed with connection pooling (max 5 concurrent)
- Batch processing prevents overwhelming the server

### Error Handling

- Network errors: Automatic retry up to 10 times
- Invalid responses: Logged and skipped
- Failed jobs tracked separately for batch retry

### CSV Output

- UTF-8 encoding for Bengali characters
- Dynamically generated columns (future-proof for new API fields)
- Alphabetically sorted columns for consistency
- HTML tags stripped for readability

## Contributing

This project is for educational purposes. If you find issues or improvements, feel free to open an issue or PR.

## License

Educational use only. Respect BDJobs.com's terms of service.
