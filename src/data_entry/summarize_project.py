# Author: Alden Sahi
# Date: 09/25/2026
# Program Name: summarize_project
# Project Description: Summarizes a project based on commit summaries

from pathlib import Path
import json
import sys
from typing import Any
from SummarizationLLM import SummarizationLLM

MODEL_NAME = "gemma4"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMMIT_LOG = REPO_ROOT / "src" / "data_store" / "COMMIT_SUMMARY_LOG.jsonl"
PROJECT_LOG = REPO_ROOT / "src" / "data_store" / "PROJECT_SUMMARY_LOG.json"

def get_commit_summaries(project_id: str) -> list[dict[str, Any]]:
    """Loads commit summaries for a specific project from the commit log.

    Returns:
        list[dict[str, Any]]: Commit summary records whose project_id matches.
    """
    
    # Loads all commits
    summaries = []
    with COMMIT_LOG.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                summaries.append(json.loads(line))
            
    # Filters project commit summaries
    project_summaries = [s for s in summaries if s.get("project_id") == project_id]
    
    return project_summaries

    
def main() -> int:
    if len(sys.argv) != 2:
        print("usage: summarize_project.py <project_id>", file=sys.stderr)
        return 2
    
    project_id = sys.argv[1]
    commit_summaries = get_commit_summaries(project_id)

    
    if not commit_summaries:
        print(f"No commit summaries found for {project_id}", file=sys.stderr)
        return 1
   
   
    print(f"Found {len(commit_summaries)} commit summaries for {project_id}", file=sys.stderr)
    agent = SummarizationLLM(MODEL_NAME)
    output = agent.summarize_project(json.dumps(commit_summaries, indent=2))
    output_as_dict = output.model_dump()
    record = {"project_id": project_id, **output_as_dict}   # unpacks all kv pairs inside new dictionary
    
    # Loads all project summarize, update, and save new log
    profiles = json.loads(PROJECT_LOG.read_text(encoding="utf-8")) if PROJECT_LOG.exists() else {}
    profiles[project_id] = output.model_dump()
    PROJECT_LOG.write_text(json.dumps(profiles, indent=4), encoding="utf-8")


    print(f"Summarized {len(commit_summaries)} commits-> {project_id}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())