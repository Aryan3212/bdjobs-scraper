#!/usr/bin/env python3
"""Quick test with configurable job count"""
import asyncio
import sys
import os
sys.path.insert(0, '.')

# Import the main scraper but override some settings
from scraper import bdjobs

# Test configuration
TEST_PAGES = 1        # How many pages to fetch (50 jobs per page)
TEST_JOBS_LIMIT = 5   # Maximum jobs to process (or None for all from pages)

async def test_main():
    """Modified main function for testing"""
    global TEST_PAGES, TEST_JOBS_LIMIT
    
    print(f"🧪 TEST MODE: Fetching {TEST_PAGES} page(s), processing up to {TEST_JOBS_LIMIT or 'all'} jobs\n")
    
    # Create session
    conn = bdjobs.aiohttp.TCPConnector(limit=5)
    session = bdjobs.aiohttp.ClientSession(connector=conn)
    
    # Get first page
    print("Fetching job list...")
    first_page = await bdjobs.fetch_job_list_page(1, session)
    
    if not first_page or first_page.get('statuscode') != '1':
        print("Failed to fetch job list")
        await session.close()
        return
    
    total_pages = first_page['common']['totalpages']
    total_jobs = first_page['common']['total_records_found']
    print(f'Total jobs available: {total_jobs}, Total pages: {total_pages}\n')
    
    # Collect job IDs
    all_job_ids = []
    
    # Get job IDs from first page
    for job in first_page.get('data', []):
        all_job_ids.append(job['Jobid'])
    for job in first_page.get('premiumData', []):
        all_job_ids.append(job['Jobid'])
    
    # Fetch additional pages if requested
    for page_num in range(2, min(TEST_PAGES + 1, total_pages + 1)):
        print(f'Fetching page {page_num}...')
        page_data = await bdjobs.fetch_job_list_page(page_num, session)
        
        if page_data and page_data.get('statuscode') == '1':
            for job in page_data.get('data', []):
                all_job_ids.append(job['Jobid'])
            for job in page_data.get('premiumData', []):
                all_job_ids.append(job['Jobid'])
    
    # Apply test limit
    if TEST_JOBS_LIMIT:
        all_job_ids = all_job_ids[:TEST_JOBS_LIMIT]
    
    print(f'\n📋 Processing {len(all_job_ids)} jobs: {all_job_ids}\n')
    
    # Process jobs
    jobs_data = []
    for i, job_id in enumerate(all_job_ids, 1):
        print(f'[{i}/{len(all_job_ids)}] Fetching job {job_id}...')
        job_data = await bdjobs.process_job(job_id, session)
        
        if job_data:
            print(f'  ✓ {job_data.get("job_title")} at {job_data.get("company_name")}')
            jobs_data.append(job_data)
        else:
            print(f'  ✗ Failed')
    
    # Write to CSV
    timestamp = bdjobs.datetime.timestamp(bdjobs.datetime.now())
    csv_path = f'dataset/bdjobs-test-{timestamp}.csv'
    
    fieldnames = sorted(list(bdjobs.all_fields))
    
    with open(csv_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = bdjobs.csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(jobs_data)
    
    print(f'\n✅ Successfully scraped {len(jobs_data)} jobs')
    print(f'📁 Output: {csv_path}')
    
    await session.close()

if __name__ == "__main__":
    if not os.path.exists('./dataset/'):
        os.mkdir('dataset')
    asyncio.run(test_main())
