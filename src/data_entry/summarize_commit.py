# Author: Alden Sahi
# Date: 07/29/2026
# Program Name: summarize_commit
# Project Description: CLI entrypoint invoked by the pre-push hook. Given a commit
    # sha, diffs it against its parent, asks SummarizationLLM to extract structured
    # fields, and appends the result as one line to SUMMARY_LOG.jsonl.

import json
import subprocess
import sys
from pathlib import Path

from SummarizationLLM import SummarizationLLM
from utils import write_jsonl, check_for_duplicate

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMMIT_LOG_PATH = REPO_ROOT / "src" / "data_store" / "COMMIT_SUMMARY_LOG.jsonl"
MODEL_NAME = "docker.io/ai/gemma4:latest"


def get_commit_diff(commit_sha: str) -> str:
    result = subprocess.run(
        ["git", "show", "--patch", "--stat", commit_sha],       # command 
        cwd=REPO_ROOT,                                          # runs command in REPO_ROOT
        capture_output=True,                                    # saves stdout in result.stdout and stderr in result.stderr
        text=True,                                              # decodes sequential byte output as text
        check=True,                                             # raises subprocess.CalledProcessError if git exits nonzero
    )
    return result.stdout

def get_paths():
    """
        diff-tree plumbing command (meant for scripts) compares two tree obkects
        --no-commit-id suppress commit-id in output (we already know ID)
        --name-only only outputs file paths (w/o it -> raw mode lines)
        -r recurses into subdirectories. Without it, a change to src/auth/tokens.py shows up only as src changed, which is useless for your prefix signature.
        -M enables detection of renamed files.
        --name-status prefixes each path with a status letter: A added, M modified, D deleted, R renamed (with a similarity score, like R087), C copied, T type change. For renames it prints both old and new paths
        --numstat gives added<TAB>removed<TAB>path per file. Binary files show - for both counts. Handy as a weight
        <sha> is the commit hash
        
    
    """
    
def get_all_commit_hashes() -> list[str]:
    """Runs git command that gets all comit hashes from current head and parses into list

    Returns:
        list[str]: list of all commit hashes from the current head
    """
    
    result = subprocess.run(
        ["git", "log", "--pretty=format:%H"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    commit_hashes = result.stdout.strip().split("\n")
    print(f"Found {len(commit_hashes)} commit hashes.")
    return commit_hashes

def summarize_commit(commit_sha: str) -> bool:
    """Summarize commit passing diffs as context and summarization 
       using LLM into structured format, saves to commit log file

    Args:
        commit_sha (str): commit hash

    Returns:
        bool: True if the commit was successfully summarized and saved, False if it was already in the log or failed to summarize
    """
    
    # Gets new changes in commit
    diff = get_commit_diff(commit_sha)

    # Exits if commit is already in the log
    test_dict = {"project_id": REPO_ROOT.name, "commit": commit_sha}
    if check_for_duplicate("CommitSummaries", test_dict):
        return False
    
    # Summarizes diffs
    agent = SummarizationLLM(MODEL_NAME)
    output = agent.summarize_commit(diff)
    output_as_dict = output.model_dump()
    
    # Appends the new commit summary to the commit log file
    record = {**test_dict, **output_as_dict}   # unpacks all kv pairs inside new dictionary
    if write_jsonl("CommitSummaries", record):
        print(f"Summarized {commit_sha[:8]} -> {COMMIT_LOG_PATH.name}")
    else:
        print(f"Failed to summarize {commit_sha[:8]}")
        return False
    
    return True
    
def summarize_all_commits() -> None:
    """Summarizes all commits in the repository by iterating through all commit hashes and calling summarize_commit for each."""
    commit_hashes = get_all_commit_hashes()
    for commit_sha in commit_hashes:
        summarize_commit(commit_sha)
    print("Finished summarizing all commits for this project")

def main() -> int:

    while True:
        print("\n Welcome to Commit Summarization Menu :)")
        print("1. Summarize a single commit")
        print("2. Summarize all commits")
        print("3. Exit\n")
        choice = input("Enter your choice: ")
        
        match choice:
            case "1":
                commit_sha = input("Enter the commit hash: ")
                print()
                summarize_commit(commit_sha)
            case "2":
                print()
                summarize_all_commits()
            case "3":
                break
            case _:
                print("Invalid choice, please try again.")
                print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
