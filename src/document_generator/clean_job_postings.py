# Author: Alden Sahi
# Date: 09/28/2026
# Program Name: clean_job_postings

from pathlib import Path
import json





REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMMIT_LOG_PATH = REPO_ROOT / "src" / "data_store" / "job_details.json"

with COMMIT_LOG_PATH.open("r", encoding="utf-8") as f:
    job_data = json.load(f)
    
    for job in job_data:
        print(job["text"])
        print(job["comments"])
        if input("Coninue?: ") == "no":
            exit()
            
            
