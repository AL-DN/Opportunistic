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

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
COMMIT_LOG_PATH = REPO_ROOT / "src" / "data_store" / "COMMIT_SUMMARY_LOG.jsonl"
MODEL_NAME = "gemma4"


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


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: summarize_commit.py <commit_sha>", file=sys.stderr)
        return 2

    # Gets new changes in commit
    commit_sha = sys.argv[1]
    diff = get_commit_diff(commit_sha)

    # structured summary of code changes
    agent = SummarizationLLM(MODEL_NAME)
    output = agent.summarize_commit(diff)
    output_as_dict = output.model_dump()
    output_as_dict["project_id"] = REPO_ROOT.name   # attaches project directory name where commit was ran
    record = {"commit": commit_sha, **output_as_dict}   # unpacks all kv pairs inside new dictionary
    
    # Appends the new commit summary to the commit log file
    with COMMIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    print(f"Summarized {commit_sha[:8]} -> {COMMIT_LOG_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
