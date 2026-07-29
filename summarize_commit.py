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

REPO_ROOT = Path(__file__).resolve().parent
LOG_PATH = REPO_ROOT / "SUMMARY_LOG.jsonl"
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


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: summarize_commit.py <commit_sha>", file=sys.stderr)
        return 2

    commit_sha = sys.argv[1]
    diff = get_commit_diff(commit_sha)

    agent = SummarizationLLM(MODEL_NAME)
    output = agent.summarize(diff)

    record = {"commit": commit_sha, **output.model_dump()}
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

    print(f"Summarized {commit_sha[:8]} -> {LOG_PATH.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
