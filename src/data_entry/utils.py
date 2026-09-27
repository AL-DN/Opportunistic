# Author: Alden Sahi
# Date: 09/26/2026
# Program Name: utils.py
# Decription: Helper functions to manipulate data

from pathlib import Path
import json
from typing import Any, Literal, Optional
from pydantic import validate_call, BaseModel, ConfigDict


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMMIT_LOG = REPO_ROOT / "src" / "data_store" / "COMMIT_SUMMARY_LOG.jsonl"
PROJECT_LOG = REPO_ROOT / "src" / "data_store" / "PROJECT_SUMMARY_LOG.jsonl"


Data = Literal["CommitSummaries", "ProjectSummaries"]

class CommitRecord(BaseModel):
    model_config = ConfigDict(extra="allow")  # changes pydantic model config to allow for extra fields ( we are only concered with project_id and commit)
    commit: str
    project_id: str

class ProjectRecord(BaseModel):
    model_config = ConfigDict(extra="allow")  # changes pydantic model config to allow for extra fields ( we are only concered with project_id and commit)
    project_id: str
    
    

@validate_call(validate_return=True, config={"strict": True})
def read_log(data: Data)->list[dict[str,Any]]:
    
    if data == "CommitSummaries": 
        
        if not COMMIT_LOG.exists():
            return []
        with COMMIT_LOG.open(encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
        
    elif data == "ProjectSummaries":
        
        if not PROJECT_LOG.exists():
            return []
        with open(PROJECT_LOG, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
        

def initialize_project_log(project_id: str) -> dict[str, str]:
    """On new project summary, attach to work experience if possible for ease of resume building

    Returns:
        dict[str, str]: inital project log dictionary
    """
    project_log = {}
    print("Project Type:")
    print("1. Project")
    print("2. Work Experience")
    while True:
        project_type = input("Enter project type (1 or 2):")
        match project_type:
            case "1":
                # handle project type
                project_log["project_id"] = project_id
                project_log["type"] = "project"
                break
            case "2":
                # handle work experience type
                project_log["project_id"] = project_id
                project_log["type"] = "work_experience"
                project_log["title"] = input("Enter title: ")
                project_log["start_date"] = input("Enter start date(MM-DD-YYYY): ")
                project_log["end_date"] = "Present"
                break
            case _:
                print("Invalid project type")
    return project_log

@validate_call(validate_return=True, config={"strict": True})
def write_jsonl(data: Data, record: dict[str,Any])->bool:
    """Validates Input, checks for duplicates. 
        Commit Summary completely skips operation on duplicate
        Project Summary rewrites the record on  duplicate.

    Args:
    
        data (Data): file to write the record to
        record (dict[str,str]): new input record to be written to the log file

    Returns:
        bool: True if the record was written successfully, False if it was a duplicate.
    """
    
    
    # Write to COMMIT LOG
    if data == "CommitSummaries":
        
        CommitRecord.model_validate(record)                             # Validate the record against the CommitRecord model 
        key = (record["project_id"], record["commit"])                  # extracts project_id and commit as key from attempt record
        
        if COMMIT_LOG.exists():
            with COMMIT_LOG.open("r", encoding="utf-8") as f:
                
                for line in f:
                    if not line.strip():
                        continue
                    
                    r = json.loads(line)                               # Loads commit record line by line (reduces memory usage, avoids loading the entire file into memory)
                    if (r["project_id"], r["commit"]) == key:          # if there is a matching key then do not save commit message again
                        print(f"Duplicate record found.")
                        return False
        
        with COMMIT_LOG.open("a", encoding="utf-8") as f:           # Appends ( we ensured uniqueness by checking for duplicates above) to commit log
            f.write(json.dumps(record) + "\n")
        print(f"Record written successfully")
        return True
    
    elif data == "ProjectSummaries":
        ProjectRecord.model_validate(record)                                            # Validate the record against the ProjectRecord model
        attempted_project_id = record["project_id"]                                     # Project ID of the record being attempted
        project_summaries = read_log("ProjectSummaries")                                # Read project summaries from the log file
        
        replaced = False
        for idx, log in enumerate(project_summaries):
            if log["project_id"] == record["project_id"]:                               # if there is already an entry, overwrite LLM Output
                project_summaries[idx] = {**log, **record}
                replaced = True
                print(f"Freshened Summary for project {attempted_project_id}") 
                return True
            
        if not replaced:                                                               #  if its a new entry entirely, initalize and add LLM Output
            new_project_log = initialize_project_log(attempted_project_id)
            new_project_log = {**new_project_log, **record}
                
            with PROJECT_LOG.open("w", encoding="utf-8") as f:                          # Writes Project Summary to Log
                f.write(json.dumps(new_project_log) + "\n")
                print(f"New Entry for project {attempted_project_id}")
                return True
            
    return False
        

def check_for_duplicate(data: Data, record: dict[str,Any])->bool:
    """Checks for duplicates

    Args:
        data (Data): which log file to search
        record (dict[str,str]): the record to check for duplicates
    Returns:
        bool: True if the record is a duplicate, False if it is not a duplicate.
    """
    # Write to COMMIT LOG
    if data == "CommitSummaries":
        
        CommitRecord.model_validate(record)  # Validate the record against the CommitRecord model 
        key = (record["project_id"], record["commit"])
        
        if COMMIT_LOG.exists():
            with COMMIT_LOG.open("r", encoding="utf-8") as f:
                
                for line in f:
                    if not line.strip():
                        continue
                    
                    r = json.loads(line)
                    if (r["project_id"], r["commit"]) == key:
                        print(f"Duplicate record found.")
                        return True
                
                return False
   
    return False
        
        