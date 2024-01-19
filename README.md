# This does not work as of now.
Update: I saw the current UI and don't feel like it's feasible to scrape this website anymore as of Jan 2024. The data isn't formatted or displayed properly, therefore I'm abandoning this.

Requirements:
- Python 3.10+

Commands:
- Create virtual environment: `python3 -m venv venv`
- Install dependencies: `pip install -r requirements.txt`
- Run tests: `python3 -m unittest -v tests/test.py`
- Run script: `python3 scraper/bdjobs.py`

# bdjobs-scraper
DISCLAIMER: This is obviously only for educational and research purposes.

A script to scrape BDjobs using concurrent requests, retry mechanism and efficient file I/O usage.

This script goes through the list of jobs in BDJobs, goes to the details page, extracts the important properties of each job posting and saves it to a CSV file on disk.

Requests to the website are made concurrently with 4 concurrent requests for the list page, and 15 for the details page. Doing it without using AsyncIO would take 1s * 5000 = 5000s which is 83 minutes.

Compared to that this script runs on average 10 mins so 8x increase in speed.

Along with that we're extracting all the important data using BeautifulSoup4 and saving it to disk for each detail page visit.

Although writing to disk in this way can take up more time this is much more memory efficient as we're only storing 1 page in memory each time and not 5000 pages all together and dumping them.

Moreover, I put in a simple retry mechanism for any failed requests, that might happen due to timeouts. I just put back the requested URL in a queue where it is processed later.

My reason for doing this was to get an idea of the job market in Bangladesh in recent times, so I needed the data.
