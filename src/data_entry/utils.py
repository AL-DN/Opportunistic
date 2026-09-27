# Author: Alden Sahi
# Date: 09/26/2026
# Program Name: utils.py
# Decription: Helper functions to manipulate data

from pathlib import Path
import json
from typing import Literal
from pydantic import validate_call, BaseModel, ConfigDict


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMMIT_LOG = REPO_ROOT / "src" / "data_store" / "COMMIT_SUMMARY_LOG.jsonl"
PROJECT_LOG = REPO_ROOT / "src" / "data_store" / "PROJECT_SUMMARY_LOG.json"


Data = Literal["CommitSummaries", "ProjectSummaries"]

class CommitRecord(BaseModel):
    model_config = ConfigDict(extra="allow")  # changes pydantic model config to allow for extra fields ( we are only concered with project_id and commit)
    commit: str
    project_id: str
    

@validate_call(validate_return=True, config={"strict": True})
def read_log(data: Data)->list[dict[str,str]]:
    
    if data == "CommitSummaries": 
        
        if not COMMIT_LOG.exists():
            return []
        with COMMIT_LOG.open(encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
        
    elif data == "ProjectSummaries":
        
        if not COMMIT_LOG.exists():
            return []
        with open(PROJECT_LOG, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
        

def write_jsonl(data: Data, record: dict[str,str])->bool:
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
                        return False
        
        with COMMIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        
        print(f"Record written successfully")
        return True
    return False
        

def check_for_duplicate(data: Data, record: dict[str,str])->bool:
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
        
        