from datetime import datetime
from bs4 import BeautifulSoup
import csv
import asyncio
import aiohttp
import os
import json


MAX_RETRIES = 10
LIST_API_URL = 'https://gateway.bdjobs.com/recruitment-account-test/api/JobSearch/GetJobSearch'
DETAILS_API_URL = 'https://gateway.bdjobs.com/ActtivejobsTest/api/JobSubsystem/jobDetails'

retry = []
all_fields = set()  # Track all fields we encounter for dynamic CSV columns


async def fetch_json(url, session):
    """Fetch JSON from API endpoint"""
    async with session.get(url) as resp:
        if resp.status == 200:
            return await resp.json()
        return None


def strip_html(html_text):
    """Strip HTML tags from text"""
    if not html_text:
        return None
    soup = BeautifulSoup(html_text, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    return text if text else None


def extract_job_data(job_api_response):
    """Extract and normalize job data from API response"""
    global all_fields
    
    # Map API fields to our desired field names
    job_data = {
        'job_id': job_api_response.get('JobId'),
        'company_name': job_api_response.get('CompnayName'),  # Note: API has typo "Compnay"
        'job_title': job_api_response.get('JobTitle'),
        'posted_on': job_api_response.get('PostedOn'),
        'deadline': job_api_response.get('Deadline'),
        'vacancies': job_api_response.get('JobVacancies'),
        'job_description': strip_html(job_api_response.get('JobDescription')),
        'job_nature': job_api_response.get('JobNature'),
        'job_workplace': job_api_response.get('JobWorkPlace'),
        'education_requirements': strip_html(job_api_response.get('EducationRequirements')),
        'skills_required': job_api_response.get('SkillsRequired'),
        'experience': strip_html(job_api_response.get('experience')),
        'gender': job_api_response.get('Gender'),
        'age': job_api_response.get('Age'),
        'additional_requirements': strip_html(job_api_response.get('AdditionJobRequirements')),
        'location': job_api_response.get('JobLocation'),
        'salary_range': job_api_response.get('JobSalaryRange'),
        'salary_min': job_api_response.get('JobSalaryMinSalary'),
        'salary_max': job_api_response.get('JobSalaryMaxSalary'),
        'other_benefits': strip_html(job_api_response.get('JobOtherBenifits')),
        'company_business': job_api_response.get('CompanyBusiness'),
        'company_address': job_api_response.get('CompanyAddress'),
        'company_website': job_api_response.get('CompanyWeb'),
        'company_logo': job_api_response.get('JobLOgoName'),
        'apply_email': job_api_response.get('ApplyEmail'),
        'apply_url': job_api_response.get('ApplyURL'),
        'online_apply': job_api_response.get('OnlineApply'),
        'job_source': job_api_response.get('JobSource'),
        'job_context': strip_html(job_api_response.get('Context')),
        'application_instructions': strip_html(job_api_response.get('ApplyInstruction')),
        'hard_copy_instructions': strip_html(job_api_response.get('HardCopy')),
    }
    
    # Track all fields for dynamic CSV
    all_fields.update(job_data.keys())
    
    return job_data


async def fetch_job_details(job_id, session):
    """Fetch detailed job information from API"""
    url = f'{DETAILS_API_URL}?jobId={job_id}'
    response = await fetch_json(url, session)
    
    if response and response.get('statuscode') == '0' and response.get('data'):
        return response['data'][0]  # API returns array with single item
    return None

async def fetch_job_list_page(page_num, session):
    """Fetch a page of job listings"""
    url = f'{LIST_API_URL}?isPro=1&rpp=50&pg={page_num}'
    await asyncio.sleep(0.25)  # Rate limiting
    return await fetch_json(url, session)


async def process_job(job_id, session):
    """Fetch and process a single job's details"""
    try:
        job_details = await fetch_job_details(job_id, session)
        if job_details:
            return extract_job_data(job_details)
        else:
            print(f"Failed to fetch job {job_id}")
            return None
    except Exception as e:
        print(f"Error processing job {job_id}: {repr(e)}")
        retry.append(job_id)
        return None


async def main():
    global retry, all_fields
    
    print("Starting BDJobs scraper...")
    
    # Create session
    conn = aiohttp.TCPConnector(limit=5)
    session = aiohttp.ClientSession(connector=conn)
    
    # Get first page to determine total pages
    print("Fetching job list...")
    first_page = await fetch_job_list_page(1, session)
    
    if not first_page or first_page.get('statuscode') != '1':
        print("Failed to fetch job list")
        await session.close()
        return
    
    total_pages = first_page['common']['totalpages']
    total_jobs = first_page['common']['total_records_found']
    print(f'Total jobs: {total_jobs}, Total pages: {total_pages}')
    
    # Collect all job IDs from all pages
    all_job_ids = []
    
    # Get job IDs from first page
    for job in first_page.get('data', []):
        all_job_ids.append(job['Jobid'])
    for job in first_page.get('premiumData', []):
        all_job_ids.append(job['Jobid'])
    
    # Fetch all pages
    pages_to_fetch = total_pages
    print(f'Fetching {pages_to_fetch} pages...')
    
    for page_num in range(2, pages_to_fetch + 1):
        print(f'Fetching page {page_num}/{pages_to_fetch}...')
        page_data = await fetch_job_list_page(page_num, session)
        
        if page_data and page_data.get('statuscode') == '1':
            for job in page_data.get('data', []):
                all_job_ids.append(job['Jobid'])
            for job in page_data.get('premiumData', []):
                all_job_ids.append(job['Jobid'])
    
    print(f'Collected {len(all_job_ids)} job IDs')
    
    # Fetch details for all jobs
    print('Fetching job details...')
    jobs_data = []
    
    # Process in batches to avoid overwhelming the API
    batch_size = 20
    for i in range(0, len(all_job_ids), batch_size):
        batch = all_job_ids[i:i+batch_size]
        print(f'Processing jobs {i+1} to {min(i+batch_size, len(all_job_ids))}...')
        
        tasks = [process_job(job_id, session) for job_id in batch]
        results = await asyncio.gather(*tasks)
        jobs_data.extend([r for r in results if r is not None])
        
    # Retry failed jobs
    retry_count = 0
    while len(retry) > 0 and retry_count < MAX_RETRIES:
        print(f'Retrying {len(retry)} failed jobs (attempt {retry_count + 1})...')
        retry_batch = retry.copy()
        retry = []
        
        tasks = [process_job(job_id, session) for job_id in retry_batch]
        results = await asyncio.gather(*tasks)
        jobs_data.extend([r for r in results if r is not None])
        retry_count += 1
    
    # Write to CSV with dynamic columns
    now = datetime.now()
    timestamp = datetime.timestamp(now)
    csv_path = f'dataset/bdjobs-{timestamp}.csv'
    
    # Get all unique fields from collected data
    fieldnames = sorted(list(all_fields))
    
    print(f'Writing {len(jobs_data)} jobs to CSV with {len(fieldnames)} columns...')
    
    with open(csv_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(jobs_data)
    
    print(f'Successfully scraped {len(jobs_data)} jobs')
    print(f'Output: {csv_path}')
    
    await session.close()


if __name__ == "__main__":
    if not os.path.exists('./dataset/'):
        os.mkdir('dataset')
    asyncio.run(main())
