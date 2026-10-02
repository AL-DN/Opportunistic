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
from playwright.sync_api import Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse, parse_qs
from trafilatura import fetch_url, extract


# Job HTML Parser config
from llm_config.LocalLLM import LocalLLM
from llm_config.prompt import job_html_parse_system_prompt
from llm_config.output_formats import JobProfile
load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_STORE = REPO_ROOT / "src" / "data_store"
PARSED_JOB_LOG = DATA_STORE / "PARSED_JOB_LOG.jsonl"


MODEL_NAME = "docker.io/ai/gemma4:latest"
LINKEDIN_USER = os.environ["LINKEDIN_USER"]
LINKEDIN_PASSWORD = os.environ["LINKEDIN_PASSWORD"]


def select_filter_option(page: Page, filter_button: str, option_text: str, attempts: int = 3) -> None:
    """Opens a LinkedIn search filter dropdown and selects an option, retrying if the dropdown
    collapses (LinkedIn re-renders the filter bar when results from a previous filter load).

    Args:
        page (Page): page on the LinkedIn job search results
        filter_button (str): accessible name of the filter dropdown button
        option_text (str): text of the option's <label>
        attempts (int): number of times to open the dropdown before giving up
    """
    for _ in range(attempts):
        page.get_by_role("button", name=filter_button).click()
        try:
            page.locator("label").filter(has_text=option_text).click(timeout=5000)
            return
        except PlaywrightTimeoutError:
            page.keyboard.press("Escape")   # make sure the dropdown is closed before reopening
            page.wait_for_timeout(1000)
    raise PlaywrightTimeoutError(f"Could not select '{option_text}' in '{filter_button}' after {attempts} attempts")


def get_linkedin_job_urls(page: Page) -> list[tuple[str,str]]:
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
    
    select_filter_option(page, "Date posted filter. Clicking", "Past 24 hours Filter by Past")
    page.get_by_role("button", name="Apply current filter to show").click()
    time.sleep(1)

    select_filter_option(page, "Experience level filter.", "Entry level Filter by Entry")
    page.get_by_role("button", name="Apply current filter to show").click()
    time.sleep(1)

    select_filter_option(page, "Salary filter. Clicking this", "$80,000+ Filter by $80,000+")
    
    
    # Captures inital response from search
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
    with open(DATA_STORE / "job_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    # ------------------
    
    # Gets Data in Seperate network calls
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

    with open(DATA_STORE / "job_results_clean.json", "w") as f:
        json.dump(jobs, f, indent=4)
        
    print(f"Found {len(jobs)} jobs.")

    # id is important for rewrite of html(testing), and parsed data to file.
    return [(job["id"], job["jobUrl"]) for job in jobs]


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


def retrieve_job_html(page: Page, job_ids_urls: list[tuple[str,str]]) -> list[dict]:
    
    job_html = []
    for idx, (job_id, url) in enumerate(job_ids_urls):
        
        # Navigate to LinkedIn Job Page ("load" can hang on LinkedIn's trackers/ads)
        try:
            response = page.goto(url, wait_until="domcontentloaded", timeout=10000)
        except PlaywrightError as e:  # timeouts, net::ERR_ABORTED, etc.
            print(f"Failed to load linkedin job card @ URL: {url} ({e.message.splitlines()[0]})")
            continue
        time.sleep(2)

        if response and response.ok:
            
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
                html = extract(downloaded,
                                output_format="json",
                                url=apply_url,
                                include_tables=True,     # requirements are sometimes in tables
                                include_comments=False,
                                favor_recall=True,       # keep more rather than less
                                )
                
                if not html:
                    try:
                        page.goto(apply_url, wait_until="domcontentloaded", timeout=30000)
                    except PlaywrightError as e:
                        print(f"Failed to load apply page @ {apply_url} ({e.message.splitlines()[0]})")
                        continue
                    page.wait_for_timeout(2500)   # let the SPA hydrate
                    downloaded = page.content()
                    html = extract(downloaded,
                        output_format="json",
                        include_tables=True,     # requirements are sometimes in tables
                        include_comments=False,
                        favor_recall=True,       # keep more rather than less
                        )
                    if html is None:
                        print(f"Client Side extraction failed for {apply_url}")
                        continue
                    
                html = json.loads(html)  # extract() returns a JSON string
                html["job_id"] = job_id
                job_html.append(html)
                print(f"Parsed {idx+1}/{len(job_ids_urls)} Job Descriptions")
            else:
                print(f"No apply control found @ {url}")
        
    
        else:
            print(f"Failed to navigate to linkedin job card @ URL: {url}")
            
            
    return job_html

def parse_job_html(job_htmls: list[dict[str,str]]):
    
    parsed_jobs = []
    
    # LLM Setup
    job_parser = LocalLLM(MODEL_NAME)
    
    for entry in job_htmls:
        html = entry["text"]
        output = job_parser.output_structured_format(
                system_prompt=job_html_parse_system_prompt,
                user_prompt=html,
                output=JobProfile
                )
        output_as_dict = output.model_dump()
        
        result = {**entry, **output_as_dict}
        parsed_jobs.append(result)
        
    with PARSED_JOB_LOG.open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in parsed_jobs)
    print(f"{len(job_htmls)} job applications parsed.")
        
    
           

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    
    page = context.new_page()
    page.set_default_timeout(80000)
    job_ids_urls = get_linkedin_job_urls(page)
    page.close()
    
    page = context.new_page()
    page.set_default_timeout(80000)
    html = retrieve_job_html(page, job_ids_urls)
    page.close()
    
    with open(DATA_STORE / "job_html.json", "w") as f:
        json.dump(html, f, indent=4)
    page.close()
    context.close()
    browser.close()
    
    parse_job_html(html)


with sync_playwright() as playwright:
    run(playwright)


