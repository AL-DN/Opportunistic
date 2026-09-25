# Author: Alden Sahi
# Date: 09/11/2026
# Program Name: test-playwright.py
# Project Description:
    # 1. Login in MyGreenhouse
    # 2. Enter a job search query
    # 3. catch response from network
    # Save Results to JSON
    
    
import re
from playwright.sync_api import Playwright, sync_playwright, expect
import time
import json


def run(playwright: Playwright) -> None:
    
    # Launch browser and start new independent window
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://my.greenhouse.io/users/sign_in")
    
    # Login to MyGreenhouse
    page.get_by_role("textbox", name="Email").click()
    page.get_by_role("textbox", name="Email").press_sequentially("a1dencode101@gmail.com")
    page.get_by_role("textbox", name="Email").press("Enter")
    page.get_by_role("button", name="Send security code").click()
    page.pause()                                                                    # Wait for user to enter security code manually

    
    # Wipe any existing search params
    page.get_by_role("button", name="Reset filters").click()            # Clear misc filters
    page.get_by_role("button", name="Clear", exact=True).click()        # Clear Job Title
    page.get_by_role("button", name="Clear Selections").click()         # Clear Location

    
    # Fill Search Params
    page.get_by_role("textbox", name="Search for a job title").click()                                      # Job Title
    page.get_by_role("textbox", name="Search for a job title").press_sequentially("Software Engineer")
    time.sleep(1)
    
    page.locator(".select__input-container").click()                                                        # Location
    page.locator("#react-select-2-input").fill("new york")
    page.get_by_role("option", name="New York, NY, USA").click()
    time.sleep(1)

    
    page.get_by_role("button", name="Date posted").click()                                                  # Date Posted
    page.get_by_text("Within 10 day").click()
    page.locator("html").click()
    time.sleep(1)

    
    page.get_by_role("button", name="Salary").click()                                                       # Salary
    page.get_by_role("radio", name="$40,000+").click()
    """
    page.get_by_role("radio", name="< $").click()
    page.get_by_role("radio", name="$40,000+").click()
    page.get_by_role("radio", name="$60,000+").click()
    page.get_by_role("radio", name="$200,000+").click()
    """              
    page.locator("html").click()
    time.sleep(1)

    
    page.get_by_role("button", name="Work type").click()
    page.get_by_role("checkbox", name="In person").check()             # Remote, In person, Hybrid
    page.locator("html").click()
    time.sleep(1)

    
    page.get_by_role("button", name="Employment type").click()
    page.get_by_role("checkbox", name="Full time").check()          # Full time, Part time, Contract, Temporary, Internship
    page.locator("html").click()
    time.sleep(1)

    
    
    """
    Two random function while misc get_by_role("radio) is activated that do not click buttons but can look less programtic if used
    page.get_by_text("< $40,000$40,000+$60,000+$80,").click()
    page.get_by_role("menu", name="Salary ($160,000+)").click()
    """
    
    page.get_by_role("button", name="Search").click() 
    
    results = []
    page.on("response", lambda r:
        results.append(r.json())
        if "/jobs/search" in r.url and r.request.resource_type in ("xhr", "fetch")
        else None)

    page.get_by_role("button", name="Search").click()
    page.wait_for_timeout(3000)   # let the response land

    data = results[0]
    with open("./src./data_store/job_results.json", "w") as f:
        json.dump(data, f, indent=4)


    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
