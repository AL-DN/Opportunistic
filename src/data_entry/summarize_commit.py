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

# LLM Config for Commit Summarization
from llm_config.LocalLLM import LocalLLM
from llm_config.prompt import commit_summarization_system_prompt
from llm_config.output_formats import CommitSummarizationOutputFormat


from data_entry.utils import write_jsonl, check_for_duplicate

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMMIT_LOG_PATH = REPO_ROOT / "src" / "data_store" / "COMMIT_SUMMARY_LOG.jsonl"
MODEL_NAME = "docker.io/ai/gemma4:latest"

def get_git_config(key: str) -> str:
    """Runs git config command with error handling.

    Args:
        key (str): any git config attribute

    Returns:
        str: result
    """
    try:
        result = subprocess.run(
            # command
            ["git", "config", key],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:                                                                       # returncode for key not set
            sys.exit(f"No {key} found. Set it with: git config --global {key} <value>")              # prints and exits with exit code 1 (sys.exit becuase config error not my code)
        raise                                                                                       # re-raise any other error
        
    value = result.stdout.strip()
    if not value:
        sys.exit(f"{key} is set but empty. Set it with: git config --global {key} <value>")         # prints and with exit code 1 ( exit with sys.exit because it is a config error no the code)
    return value

def get_commit_diff(commit_sha: str) -> str:
    """Generate """
    # NOTE EDGE CASE UNCOVERED: git show prits combine diff on clean merge commits it shows almost nothing, add --first-parent to diff the merge againts the branch it was mered into"""
    
    try:
        result = subprocess.run(
            # command
            ["git", "show",                                         # prints git object header 
            "--patch",                                              # full line by line diffs with + for added lines and - for removed ones
            "--stat",                                               # short summary of changed fqiles and line counts 
            commit_sha],
            cwd=REPO_ROOT,                                          # runs command in REPO_ROOT
            capture_output=True,                                    # saves stdout in result.stdout and stderr in result.stderr
            text=True,                                              # decodes sequential byte output as text
            check=True,                                             # raises subprocess.CalledProcessError if git exits nonzero
        )
        
    except subprocess.CalledProcessError as e:
        if e.returncode == 128:                                     # Can be git repo not found / commit key not found 
            print(f"Commit: {commit_sha[:8]} had error: {e.stderr.strip()}")
            return ""
        raise
        
    value = result.stdout.strip()                       
    if not value:                                                   # NOTE Will basically never trigger header is always there
        print(f"Commit: {commit_sha[:8]} had no diffs.")
        return ""      
                  
    return value

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
    try:
        result = subprocess.run(
            ["git", "log", "--pretty=format:%H"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        if e.returncode == 128:
            sys.exit(e.stderr)
        raise
            
    commit_hashes = result.stdout.strip().split("\n")
    print(f"Found {len(commit_hashes)} commit hashes.")
    return commit_hashes

def summarize_commit(rewrite: bool, commit_sha: str) -> bool:
    """Summarize commit passing diffs as context and summarization 
       using LLM into structured format, saves to commit log file

    Args:
        commit_sha (str): commit hash

    Returns:
        bool: True if the commit was successfully summarized and saved, False if it was already in the log or failed to summarize
    """
    
    # Gets new changes in commit
    diff = get_commit_diff(commit_sha)
    if not diff:                            # errors in get_commit_diff return "" to avoid summarizing nothing
        return False

    """
    Handling the rewrite param dn duplicates in COMMIT_SUMMARY_LOG.jsonl
    | rewrite | duplicate |       function       |
    |---------|-----------|----------------------|
    |    T    |     T     |   summarize,replace  | find and overwrite mid write loop, exit early
    |    T    |     F     |   summarize,append   | exhaustively searched no duplicate found in write loop 
    |    F    |     T     |         skip         | 
    |    F    |     F     |   summarize,append   | exhaustively searched no duplicate found in write loop 
    """
    
    test_dict = {"project_id": REPO_ROOT.name, "commit": commit_sha}
    skip: bool = not rewrite and check_for_duplicate("CommitSummaries", test_dict)
    if skip:
        print(f"Skipping {commit_sha[:8]}")
        return False
    
    # Summarizes diffs
    local_llm = LocalLLM(MODEL_NAME)
    output = local_llm.output_structured_format(
        system_prompt=commit_summarization_system_prompt,
        user_prompt=diff,
        output=CommitSummarizationOutputFormat
        )
    output_as_dict = output.model_dump()
    
    # Appends the new commit summary to the commit log file
    record = {**test_dict, **output_as_dict}   # unpacks all kv pairs inside new dictionary
    if write_jsonl("CommitSummaries", record, rewrite):
        print(f"Summarized {commit_sha[:8]} -> {COMMIT_LOG_PATH.name}")
    else:
        print(f"Failed to summarize {commit_sha[:8]}")
        return False
    
    return True
    
def summarize_all_commits(rewrite: bool) -> None:
    """Summarizes all commits in the repository by iterating through all commit hashes and calling summarize_commit for each."""
    success_count: int = 0
    commit_hashes = get_all_commit_hashes()

    for commit_sha in commit_hashes:
        if summarize_commit(rewrite, commit_sha):
            success_count += 1
    print(f"\nFound {len(commit_hashes) - success_count} duplicate commits for this project")        
    print(f"Summarized {success_count}/{len(commit_hashes)} commits for this project")


