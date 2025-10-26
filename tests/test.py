import unittest
import asyncio
from scraper import bdjobs


class TestBDJobsScraper(unittest.TestCase):
    def test_api_response_parser(self):
        # Mock API response structure from the new bdjobs API
        mock_api_response = {
            "statuscode": "0",
            "message": "Success",
            "data": [{
                "JobId": "1422091",
                "CompnayName": "MOS DESIGN AND MANUFACTURE",
                "JobTitle": "Officer - Sales and Marketing",
                "PostedOn": "Oct 25, 2025",
                "Deadline": "Nov 5, 2025",
                "JobVacancies": "20",
                "JobDescription": "<p>Market Research & Business Development</p>",
                "JobNature": "Full Time",
                "JobWorkPlace": "Work at office",
                "EducationRequirements": "<ul><li>Bachelor of Science (BSc)</li></ul>",
                "SkillsRequired": "Sales & Marketing",
                "experience": "<ul><li>At least 2 years</li></ul>",
                "Gender": "M",
                "AdditionJobRequirements": "<ul><li>Only Male</li></ul>",
                "JobLocation": "Anywhere in Bangladesh, Dhaka (Banani, Doyagonj)",
                "JobSalaryRange": "Tk. 15000 - 25000 (Monthly)",
                "JobOtherBenifits": "<ul><li>Performance Bonus</li></ul>",
                "CompanyBusiness": "Design and manufacturing company",
                "CompanyAddress": "49/A/1, Sharatgupta Road, Doyaganj Mor",
                "CompanyWeb": "https://mosdm.com/",
                "JobLOgoName": "https://corporate.bdjobs.com/logos/134086_1.jpg"
            }]
        }
        
        result = bdjobs.extract_job_data(mock_api_response['data'][0])
        
        # Verify key fields are extracted
        self.assertEqual(result['job_id'], '1422091')
        self.assertEqual(result['company_name'], 'MOS DESIGN AND MANUFACTURE')
        self.assertEqual(result['job_title'], 'Officer - Sales and Marketing')
        self.assertEqual(result['deadline'], 'Nov 5, 2025')
        self.assertEqual(result['vacancies'], '20')
        self.assertEqual(result['job_nature'], 'Full Time')
        self.assertEqual(result['location'], 'Anywhere in Bangladesh, Dhaka (Banani, Doyagonj)')
        self.assertEqual(result['salary_range'], 'Tk. 15000 - 25000 (Monthly)')
        self.assertIn('job_description', result)
        self.assertIn('education_requirements', result)
    
    def test_list_api_response_structure(self):
        # Mock list API response structure this test is useless just keeping it for reference
        mock_list_response = {
            "statuscode": "1",
            "message": "Success",
            "data": [{
                "Jobid": "1422091",
                "jobTitle": "Test Job",
                "companyName": "Test Company",
                "deadline": "Nov 5, 2025",
                "location": "Dhaka"
            }],
            "premiumData": [{
                "Jobid": "1422092",
                "jobTitle": "Premium Test Job"
            }],
            "common": {
                "total_records_found": 5415,
                "totalpages": 109,
                "total_vacancies": 21859
            }
        }
        
        # Verify structure is valid
        self.assertEqual(mock_list_response['statuscode'], '1')
        self.assertIn('data', mock_list_response)
        self.assertIn('premiumData', mock_list_response)
        self.assertIn('common', mock_list_response)
        self.assertGreater(len(mock_list_response['data']), 0)
        self.assertEqual(mock_list_response['data'][0]['Jobid'], '1422091')

if __name__ == '__main__':
    unittest.main(verbosity=2)
