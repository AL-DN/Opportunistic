# Author: Alden Sahi
# Date: 07/29/2026
# Program Name: SummarizationLLM
#! Project Description: Builds a class that allows for LLM initalization, and
    # summary generation given a git commit

import requests
import json
from pydantic import BaseModel, Field
from typing import Dict, Union, Any


class CommitSummarizationOutputFormat(BaseModel):
    libraries: list[str] = Field(description="Third-party libraries imported/used in the code")
    data_structures: list[str] = Field(description="Data structures utilized (e.g. list, hash map, tree)")
    bigo_time_complexity: str = Field(description="Big O time complexity of the core algorithm")
    bigo_space_complexity: str = Field(description="Big O space complexity of the core algorithm")
    result: str = Field(description="Explanation of how this improved the existing solution, or the outcome if newly written")

class ProjectProfileOutputFormat(BaseModel):
    industry: str = Field(description="Industry that technology will effect")
    one_line_summary: str = Field(
            description="One sentence a non-specialist recruiter could understand"
        )
    technical_archetypes: list[str] = Field(
        min_length=1,
        description=(
            "Industry-recognizable categories this project is an instance of, phrased in the "
            "vocabulary an employer would search for or recognize. Abstract away from this "
            "project's specifics: prefer 'one-shot LLM summarization pipeline' over 'git "
            "commit summarizer', 'semantic clustering' over 'grouping my commits'. 3-8 entries."
        ),
    )
    key_design_decisions: list[str] = Field(
        default_factory=list,
        description="Notable choices and their tradeoffs, e.g. 'path-based TF-IDF over embeddings for structural signal'",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Real constraints that shaped the design: latency, cost, privacy, data volume, offline use",
    )
    



class SummarizationLLM:

    # Constructor Definition
    def __init__(self, name: str):
        self.name = name
        self.api = f"http://localhost:12434/engines/llama.cpp/v1/chat/completions"
        self.commit_system_prompt = """
            You are a helpful assistant tasked to extract important values from this code including,
            a project_id (parent folder name), libraries, data structures and algorithms utilized. Along with big O space and time complexity along with a result
            string that explains How did it improve the current or if new what did this result in.
        """
        self.project_summarization_system_prompt = """
            You are a helpful assistant tasked to summarize the technology built in serveral stages. Please summarize
            using a combination of general technical topics that can be adjacent to other technologies in different domains.
        """


    def summarize_commit(self, prompt: str)-> CommitSummarizationOutputFormat:
        """_summary_

        Args:
            prompt (str): Retrived context from SUMMARY_LOG.jsonl

        Returns:
            OutputFormat: _description_
        """
        data: dict[str, Any] = {
            "model": f"{self.name}",
            "messages": [
                {
                    "role": "system",
                    "content": self.commit_system_prompt
                },
                {
                    "role": "user",
                    "content": f"{prompt}"
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "OutputFormat",
                    "schema": CommitSummarizationOutputFormat.model_json_schema()
                }
            }
        }
        response = requests.post(f"{self.api}", json=data)
        response.raise_for_status()
        
        body = response.json()
        choice = body["choices"][0]
        if choice["finish_reason"] == "length":
            raise RuntimeError(
                f"Output truncated at token limit (usage: {body.get('usage')})"
            )
        content = choice["message"]["content"]        
        return CommitSummarizationOutputFormat.model_validate_json(content)

    def summarize_project(self, prompt: str)-> ProjectProfileOutputFormat:
            """_summary_
    
            Args:
                prompt (str): Retrived context from SUMMARY_LOG.jsonl
    
            Returns:
                OutputFormat: _description_
            """
            data: dict[str, Any] = {
                "model": f"{self.name}",
                "messages": [
                    {
                        "role": "system",
                        "content": self.project_summarization_system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"{prompt}"
                    }
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "OutputFormat",
                        "schema": ProjectProfileOutputFormat.model_json_schema()
                    }
                }
            }
            response = requests.post(f"{self.api}", json=data)
            response.raise_for_status()
            body = response.json()
            choice = body["choices"][0]
            if choice["finish_reason"] == "length":
                raise RuntimeError(
                    f"Output truncated at token limit (usage: {body.get('usage')})"
                )
                        
            content = choice["message"]["content"]
            return ProjectProfileOutputFormat.model_validate_json(content)




if __name__ == "__main__":
    agent = SummarizationLLM("ai/qwen3.5:9B-UD-Q4_K_XL")
