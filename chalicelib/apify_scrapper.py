import json
from apify_client import ApifyClient
# import os
# os.chdir('/Users/zhuolundu/Desktop/apify/job_match')
from chalicelib.db import generate_unique_id


class ApifyScraper:
    def __init__(self, api_token: str, actor_id: str):
        self.client = ApifyClient(api_token)
        self.actor_id = actor_id

        self.dataset_obj = None

    def run_scraper(self, run_input: dict):
        try:
            run = self.client.actor(self.actor_id).call(run_input=run_input)
            self.dataset_obj = self.client.dataset(run["defaultDatasetId"])
        except Exception as e:
            print(f"Error during scraping: {e}")
            raise

    def save_results_to_json(self, filename='result.json'):
        if self.dataset_obj is None:
            print("Please run scraper before saving results.")

        gen_list = list(self.dataset_obj.iterate_items())
        with open(filename, 'w') as f:
            json.dump(gen_list, f, indent=4)
        print(f"JSON file '{filename}' created successfully!")

    def print_results(self):
        if self.dataset_obj is None:
            print("Please run scraper before printing results.")
            return

        for item in self.dataset_obj.iterate_items():
            print(item)


class JobScraper(ApifyScraper):

    def __init__(self, api_token, actor_id, **kwargs):
        # Call the parent class constructor with the api_token and actor_id
        super().__init__(api_token, actor_id)

        # Initialize JobScraper specific attributes
        self.scraper_specific_settings = kwargs

    def prepare_run_input(self):
        # Base run_input with settings common to all scrapers
        run_input = {
            **self.scraper_specific_settings
        }
        return run_input

    def run_scraper(self, run_input=None):
        if run_input is None:
            run_input = self.prepare_run_input()
        super().run_scraper(run_input)

    def save_job_results_to_db(self, job_db):
        if self.dataset_obj is None:
            print("Please run scraper before saving results.")
            return None

        for job_info in self.dataset_obj.iterate_items():
            job_db.add_file(
                generate_unique_id(),
                info=job_info)
        print("Job data saved to database successfully!")
