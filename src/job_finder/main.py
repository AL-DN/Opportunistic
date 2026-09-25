"""
Author: Alden Sahi
Date: 09/23/2026
Program Name: main.py
Program Description:
    1. Find Job Post URLs
    2. Scrape Job Descriptions
"""

import os
import re
from playwright.sync_api import Page, Playwright, sync_playwright, expect
import time
import json
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs

from trafilatura import fetch_url, extract



load_dotenv()

LINKEDIN_USER = os.environ["LINKEDIN_USER"]
LINKEDIN_PASSWORD = os.environ["LINKEDIN_PASSWORD"]


def get_linkedin_job_urls(page: Page) -> list[str]:
    """ Logs in and utilizes linkedins job search to return links to specific job posting cards.

    Args:
        page (Page): "new tab" independent browser process

    Returns:
        list[dict[str,str]]: links to specific linkedin job posting cards
    """

    
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
        
        
    jobs = []
    for el in data.get("included", []):
        if el.get("$type") != "com.linkedin.voyager.dash.jobs.JobPostingCard":
            continue
        urn = el.get("jobPostingUrn", "")
        if not urn:
            continue
        job_id = urn.rsplit(":", 1)[-1]
        jobs.append({
            "id": job_id,
            "title": el.get("jobPostingTitle"),
            "companyName": (el.get("primaryDescription") or {}).get("text"),
            "location": (el.get("secondaryDescription") or {}).get("text"),
            "salary": (el.get("tertiaryDescription") or {}).get("text"),
            "companyUrl": (el.get("logo") or {}).get("actionTarget"),
            "jobUrl": f"https://www.linkedin.com/jobs/view/{job_id}" if job_id else None,
        })

    with open("./src/data_store/job_results_clean.json", "w") as f:
        json.dump(jobs, f, indent=4)
        
    print(f"Found {len(jobs)} jobs.")

    return [job["jobUrl"] for job in jobs]


def unwrap_linkedin_redirect(href: str) -> str:
    """LinkedIn External Apply Link, housed in <a> tags with a redirect URL need to be parsed and decoded (% encoding) to get the actual destination URL.

    Args:
        href (str): Redirect URL from LinkedIn.

    Returns:
        str: absolute destination URL OR the original `href` if it is not a LinkedIn redirect.
    """
    
    parsed = urlparse(href)
    if "linkedin.com" in parsed.netloc and parsed.path.startswith("/safety/go"):
        return parse_qs(parsed.query).get("url", [href])[0]
    return href


def retrieve_job_details(page: Page, urls: list[str]) -> list[dict]:
    details = []
    for url in urls:
        
        # Navigate to LinkedIn Job Page
        response = page.goto(url)
        time.sleep(2)
        
        if response.ok:
            
            # Matches easy apply button and External Apply Link
            easy_apply_btn = page.get_by_role("button", name=re.compile(r"^Easy Apply", re.I)).first
            external_apply = page.get_by_role("link", name=re.compile(r"^Apply\b", re.I)).first

            if easy_apply_btn.is_visible():
                print(f"Easy Apply (skipping) @ {url}")
            elif external_apply.is_visible():
                
                # Gets External Job Posting URL
                linkedin_redirect_url = external_apply.evaluate("el => el.href")   # absolute URL
                #print(f"LinkedIn redirect URL: {linkedin_redirect_url}")
                apply_url = unwrap_linkedin_redirect(linkedin_redirect_url)
                print(f"Unwrapped apply URL: {apply_url}")
                
                # Handles ServerSide Rendered (No Crawler or Bot Detection)
                downloaded = fetch_url(apply_url) # Simple Get Request
                result = extract(downloaded,
                                output_format="json",
                                url=apply_url,
                                include_tables=True,     # requirements are sometimes in tables
                                include_comments=False,
                                favor_recall=True,       # keep more rather than less
                                )
                
                if not result:
                    page.goto(apply_url, wait_until="domcontentloaded", timeout=30000)
                    page.wait_for_timeout(2500)   # let the SPA hydrate
                    downloaded = page.content()
                    result = extract(downloaded,
                        output_format="json",
                        include_tables=True,     # requirements are sometimes in tables
                        include_comments=False,
                        favor_recall=True,       # keep more rather than less
                        )
                    if result is None:
                        print(f"Client Side extraction failed for {apply_url}")
                    
                details.append(json.loads(result))
            else:
                print(f"No apply control found @ {url}")
        
    
        else:
            print(f"Failed to navigate to linkedin job card @ URL: {url}")
            
            
    return details
        

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    
    page = context.new_page()
    page.set_default_timeout(80000)
    urls = get_linkedin_job_urls(page)
    page.close()
    
    page = context.new_page()
    details = retrieve_job_details(page, urls)
    page.close()
    
    
    with open("../src/data_store/job_details.json", "w") as f:
        json.dump(details, f, indent=4)
        
    page.close()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)


