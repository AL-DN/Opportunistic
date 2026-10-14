# Author: Alden Sahi
# Date: 09/25/2026
# Program Name: summarize_project
# Project Description: Summarizes a project based on commit summaries

from pathlib import Path
import json
import sys
from typing import Any

# Project Summarization Config
from llm_config.LocalLLM import LocalLLM
from llm_config.prompt import project_summarization_system_prompt
from llm_config.output_formats import ProjectProfileOutputFormat

from data_entry.utils import write_jsonl

MODEL_NAME = "docker.io/ai/gemma4:latest"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent           # this repo; data_store lives here
COMMIT_LOG = REPO_ROOT / "src" / "data_store" / "COMMIT_SUMMARY_LOG.jsonl"
PROJECT_LOG = REPO_ROOT / "src" / "data_store" / "PROJECT_SUMMARY_LOG.jsonl"

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

def summarize_project(project_id: str) -> bool:
    """Summarizes a project based on its commit summaries.

    Args:
        project_id (str): The ID of the project to summarize.

    Returns:
        bool: True if the project was successfully summarized and saved, False otherwise.
    """
    commit_summaries = get_commit_summaries(project_id)
    
        
    if not commit_summaries:
        print(f"No commit summaries found for {project_id}", file=sys.stderr)
        return 1
    print(f"Found {len(commit_summaries)} commit summaries for {project_id}", file=sys.stderr)
    
    
    agent = LocalLLM(MODEL_NAME)
    
    output = agent.output_structured_format(
        system_prompt=project_summarization_system_prompt,
        user_prompt=json.dumps(commit_summaries, indent=2),
        output=ProjectProfileOutputFormat)
    
    output_as_dict = output.model_dump()
    output_as_dict["project_id"] = project_id
    
    import torch
    # Embeds all technical_archetypes
    
    def resolve_device(device: str | None = "auto") -> str:
        """'auto' picks GPU if available, otherwise CPU. Any explicit value wins."""
        if device in (None, "auto"):
            if torch.cuda.is_available():
                return "cuda"
            if torch.backends.mps.is_available():  # Apple Silicon
                return "mps"
            return "cpu"
        return device

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("IEITYuan/Yuan-embedding-2.0-en", device=resolve_device())
    embd = model.encode(output_as_dict.get("technical_archetypes"), show_progress_bar=True)
    
    import numpy as np
    import os

    def save_or_append(path, key, new_embs):
        key = str(key)
        new_embs = np.atleast_2d(new_embs)
        data = dict(np.load(path)) if os.path.exists(path) else {}
        if key in data:
            data[key] = np.concatenate([data[key], new_embs])   # add rows to existing project
        else:
            data[key] = new_embs
        np.savez(path, **data)
        
    save_or_append("embeddings.npz",project_id, embd)

    data = np.load("embeddings.npz")
    vec = data[f"{project_id}"]
    print(vec)
            
    exit()
    if write_jsonl(data="ProjectSummaries", record=output_as_dict):
        print(f"Summarized project {project_id} -> {PROJECT_LOG.name}")
        return True
    else:
        print(f"Failed to summarize project {project_id}")
        return False
                        
    