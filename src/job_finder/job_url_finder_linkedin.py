import os
import re
from playwright.sync_api import Playwright, sync_playwright, expect
import time
import json
from dotenv import load_dotenv
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
    # page.get_by_role("textbox", name="Title, skill or Company").click()
    # page.get_by_role("textbox", name="Title, skill or Company").press_sequentially("Software Engineer")
    
    page.get_by_test_id("typeahead-input").click()
    page.get_by_test_id("typeahead-input").fill("Software Engineer")
    page.get_by_test_id("typeahead-input").press("Enter")
    
    
    # page.get_by_role("textbox", name="City, state, or zip code").click()
    # page.get_by_role("textbox", name="City, state, or zip code").press_sequentially("New York")
    # page.get_by_role("link", name="New York, New York, United States", exact=True).click()
    page.get_by_role("button", name="Location New York, NY (50 mi)").click()
    page.get_by_role("link", name="New York, New York, United").click()
    time.sleep(10)
    
    # page.get_by_role("button", name="Filter by Date posted").click()
    # page.locator("label").filter(has_text="Past 24 hours Filter by Past").click()
    # page.get_by_role("button", name="Apply current filter to show").click()
    page.get_by_role("button", name="Filter by Date posted").click()
    page.get_by_role("radio", name="Past 24 hours").click()
    page.get_by_role("link", name="Show results").click()
    time.sleep(1)

    # page.get_by_role("button", name="Filter by Experience level").click()
    # page.locator("label").filter(has_text="Entry level Filter by Entry").click()
    # page.get_by_role("button", name="Apply current filter to show").click()
    page.get_by_role("button", name="Filter by Experience level").click()
    page.get_by_role("checkbox", name="Entry-level").click()
    time.sleep(1)
    
    # page.get_by_role("button", name="Salary filter. Clicking this").click()
    # page.locator("label").filter(has_text="$80,000+ Filter by $80,000+").click()
    #page.get_by_role("button", name="Apply current filter to show").click()

    
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
    
    # NOTE MUST BE LAST SEARCH PARAM
    page.get_by_role("link", name="Show results").click()


    page.wait_for_timeout(5000)   # let the response land


    data = results[0] if results else {}
    with open("./src/data_store/job_results.json", "w") as f:
        json.dump(results, f, indent=4)
        

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
