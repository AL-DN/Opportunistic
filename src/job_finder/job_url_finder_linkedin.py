import os
import re
from playwright.sync_api import Playwright, sync_playwright, expect
import time
import json
from dotenv import load_dotenv

from job_description_parser import extract_job_json_ld

load_dotenv()

LINKEDIN_USER = os.environ["LINKEDIN_USER"]
LINKEDIN_PASSWORD = os.environ["LINKEDIN_PASSWORD"]

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(80000)
    page.goto("https://www.linkedin.com/jobs/")
    page.get_by_role("textbox", name="Email or phone").click()
    page.get_by_role("textbox", name="Email or phone").press_sequentially(LINKEDIN_USER)
    page.get_by_role("textbox", name="Password").click()
    page.get_by_role("textbox", name="Password").press_sequentially(LINKEDIN_PASSWORD)
    page.get_by_role("button", name="Sign in").click()
    page.goto("https://www.linkedin.com/jobs/")
    
    # Inital search params
    page.get_by_role("textbox", name="Title, skill or Company").click()
    page.get_by_role("textbox", name="Title, skill or Company").press_sequentially("Software Engineer")
    page.get_by_role("textbox", name="City, state, or zip code").click()
    page.get_by_role("textbox", name="City, state, or zip code").press_sequentially("New York")
    page.get_by_role("link", name="New York, New York, United States", exact=True).click()
    time.sleep(10)
    
    page.get_by_role("button", name="Date posted filter. Clicking").click()
    page.locator("label").filter(has_text="Past 24 hours Filter by Past").click()
    page.get_by_role("button", name="Apply current filter to show").click()
    time.sleep(1)

    page.get_by_role("button", name="Experience level filter.").click()
    page.locator("label").filter(has_text="Entry level Filter by Entry").click()
    page.get_by_role("button", name="Apply current filter to show").click()
    time.sleep(1)
    
    page.get_by_role("button", name="Salary filter. Clicking this").click()
    page.locator("label").filter(has_text="$80,000+ Filter by $80,000+").click()
    
    
    results = []

    def capture_job_results(playwright_response) -> None:
        """Given a Playwright Response object, appends matching job search results to `results`."""
        if "voyagerJobsDashJobCards" not in playwright_response.url or "q=jobSearch" not in playwright_response.url:
            return
        if "count=0" in playwright_response.url:
            return
        results.append(playwright_response.json())

    # Playwright registers capture_job_results as a callback function to an event listener
    page.on("response", capture_job_results)

    page.get_by_role("button", name="Apply current filter to show").click()
    page.wait_for_timeout(5000)   # let the response land


    data = results[0] if results else {}
    with open("./src/data_store/job_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
        
    # FOR EACH JOB
        # GO TO URL
        # Click Apply
        
    
    
    # jobs = []
    # for el in data.get("included", []):
    #     if el.get("$type") != "com.linkedin.voyager.dash.jobs.JobPostingCard":
    #         continue
    #     urn = el.get("jobPostingUrn", "")
    #     if not urn:
    #         continue
    #     job_id = urn.rsplit(":", 1)[-1]
    #     jobs.append({
    #         "id": job_id,
    #         "title": el.get("jobPostingTitle"),
    #         "companyName": (el.get("primaryDescription") or {}).get("text"),
    #         "location": (el.get("secondaryDescription") or {}).get("text"),
    #         "salary": (el.get("tertiaryDescription") or {}).get("text"),
    #         "companyUrl": (el.get("logo") or {}).get("actionTarget"),
    #         "jobUrl": f"https://www.linkedin.com/jobs/view/{job_id}" if job_id else None,
    #     })

    # with open("./src/data_store/job_results_clean.json", "w") as f:
    #     json.dump(jobs, f, indent=4)

    # for job in jobs:
    #     if not job["jobUrl"]:
    #         continue
    #     job["jsonLd"] = extract_job_json_ld(page, job["jobUrl"])

    # with open("./src/data_store/job_results_enriched.json", "w") as f:
    #     json.dump(jobs, f, indent=4)

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
