import time
from datetime import datetime
from bs4 import BeautifulSoup
import csv
import asyncio
import aiohttp
import os


MAX_RETRIES = 10
DIV_CLASSES = {
    'vacancies': 'vac',
    'job_source': 'job_source',
    'salary_range': 'salary_range',
    'job_location': 'job_loc',
    'job_requirements': 'job_req',
    'education_requirements': 'edu_req',
    'experience_requirements': 'edu_req',
    'employment_status': 'job_nat', 
    'job_modality': 'job_nat',
    'job_description': 'job_des',
}

retry = []

async def fetch_url(url, session):
    time.sleep(200)
    async with session.get(url) as resp:
        if resp.status:
            return await resp.text()

# helper function needed to unzip async function results
def flatten(list_of_elements):
    output = []
    for elem in list_of_elements:
        if type(elem) == list:
            for l in elem:
                output.append(l)
        else:
            output.append(elem)
    return output


# function to parse all the data from a job details page
async def extract_page_data(parsed_page):
    page_object = {}

    published_on = parsed_page.select('.job-summary div.panel-body > h4:first-child')
    if len(published_on) > 0:
        page_object['published_on'] = published_on[0].contents[2].strip()
    else:
        page_object['published_on'] = None

    job_title = parsed_page.select('h2.job-title')
    if len(job_title) > 0:
        page_object['job_title'] = job_title[0].get_text()
    else:
        page_object['job_title'] = None

    company_name = parsed_page.select('h3.company-name')
    if len(company_name) > 0:
        page_object['company_name'] = company_name[0].get_text()
    else:
        page_object['company_name'] = None

    for key, class_name in DIV_CLASSES.items():
        div_elements = parsed_page.find_all('div', class_=class_name)
        if len(div_elements) > 0:
            div_to_check = 0
            if len(div_elements) > 1 and (key == 'experience_requirements' or key == 'job_modality'):
                div_to_check = 1
            elem = div_elements[div_to_check]
            children = elem.find_all(recursive=True)
            if children[1]:
                trimmed = children[1].get_text().strip()
                page_object[key] = trimmed if trimmed != '' else None
            else:
                page_object[key] = None
        else:
            page_object[key] = None
    return page_object


async def parse_links(page, session):
    bdjobs_url_original = 'https://jobs.bdjobs.com/joblisting_common_init.asp?fcatId=-1&rpp=100&locationId=&iCat=0&JobType=0&JobLevel=0&JobPosting=0&JobDeadline=0&JobKeyword=&ListOrder=%27%27&Exp=0&Age=0&Gender=&GenderB=&MDate=&ver=&OrgType=0&news=0&RetiredArmy=&Workstation=&pwd=&AccessibilityAware='
    links = []
    # get all links from those listings
    bdjobs_url = f'{bdjobs_url_original}&pg={page}'
    listings_response = await fetch_url(bdjobs_url, session)
    parser = BeautifulSoup(listings_response, 'html.parser')
    for link in parser.select('a[href^=jobdetail]'):
        links.append(link.get('href'))
    return links

async def get_details_page(link, writer, session):
    try:
        page = await fetch_url(f'https://jobs.bdjobs.com/{link}', session)
    except Exception as e:
        retry.append(link)
        return None
    parsed_page = BeautifulSoup(page, 'html.parser')
    try:
        page_object = await extract_page_data(parsed_page)
    except Exception as e:
        print(f"Error while parsing the page: {repr(e)}")
    # write to a CSV file on disk
    writer.writerow(page_object)

async def main():
    global retry

    bdjobs_url_original = 'https://jobs.bdjobs.com/joblisting_common_init.asp?fcatId=-1&rpp=100&locationId=&iCat=0&JobType=0&JobLevel=0&JobPosting=0&JobDeadline=0&JobKeyword=&ListOrder=%27%27&Exp=0&Age=0&Gender=&GenderB=&MDate=&ver=&OrgType=0&news=0&RetiredArmy=&Workstation=&pwd=&AccessibilityAware='
    conn = aiohttp.TCPConnector(limit=4)
    session = aiohttp.ClientSession(connector=conn)
    # get 1st listings page
    listings_response = await fetch_url(bdjobs_url_original, session)
    # links array to store all the links we get from the listings page
    links = []

    # extract heading links from listings by parsing html
    parser = BeautifulSoup(listings_response, 'html.parser')
    for link in parser.select('a[href^=jobdetail]'):
        links.append(link.get('href'))
    
    # get the number of total pages for listings
    total_page_selector = parser.select('div.pagination ul li a')[-1]
    total_pages= int(total_page_selector.get_text().split('.')[-1])


    print('Total pages to parse: ', total_pages)
    tasks = [parse_links(page, session) for page in range(2, total_pages + 1)]
    results = await asyncio.gather(*tasks)
    
    links += flatten(results)

    # open a unique new CSV file to append to
    now = datetime.now()
    timestamp = datetime.timestamp(now)
    csv_file = open(f'bdjobs_scraper/bdjobs-{timestamp}.csv', mode='a')
    writer = csv.DictWriter(csv_file, fieldnames=['published_on', 'job_title','company_name',*DIV_CLASSES.keys()])
    writer.writeheader()

    # create a new connector object and session pool as we need to query 5000 links now
    conn_new = aiohttp.TCPConnector(limit=15)
    session_new = aiohttp.ClientSession(connector=conn_new)

    # get the job details page from the link and parse data from them
    tasks = [get_details_page(link, writer, session_new) for link in links]
    (await asyncio.gather(*tasks))
    retry_count = 0
    while len(retry) > 0 and retry_count < MAX_RETRIES:
        tasks = [get_details_page(link, writer, session_new) for link in retry]
        retry = []
        retry_count += 1
        (await asyncio.gather(*tasks))

    print(f'Outputted to bdjobs_scraper/bdjobs-{timestamp}.csv')
    # close the CSV and created sessions
    csv_file.close()
    await session_new.close()
    await session.close()



if __name__ == "__main__":
    if not os.path.exists('./bdjobs_scraper/'):
        os.mkdir('bdjobs_scraper')
    asyncio.run(main())
