# Author: Alden Sahi
# Date: 09/29/2026
# Program Namne: output_formats.py
# Program Description: A centralized location for all pydantic models

from pydantic import BaseModel, Field
import json


def display_output_format(output_format: BaseModel):
    print(output_format.model_json_schema())
    print(json.dumps(output_format.model_json_schema(), indent=2))
    
'''CODE SUMMARIZATION OUTPUTS'''
# Commit Summarization Output
class CommitSummarizationOutputFormat(BaseModel):
    libraries: list[str] = Field(description="Libraries imported/used in the code")
    data_structures: list[str] = Field(description="Data structures utilized (e.g. list, hash map, tree)")
    bigo_time_complexity: str = Field(description="Big O time complexity of the core algorithm")
    bigo_space_complexity: str = Field(description="Big O space complexity of the core algorithm")
    result: str = Field(description="Explanation of how this improved the existing solution, or the outcome if newly written")

# Project Summarization Output
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
    
    

'''Automated Browser Search/Retrieval'''
# Job HTML Parser Output   
class TechDescription(BaseModel):
    title: str = Field("Name of the technology.")
    interaction: str = Field("How does their proprietary technology interact with the world.") 
    underlying_tech:str = Field("technical description of how their their proprietary technology works")
    market_edge: str = Field("What makes this technology unique different?")

class CompanyDescription(BaseModel):
    contains_useful_info: bool = Field(description="If there is important company information then True else False")
    description: str = Field(description="2-3 sentences on what the company does.")

    technologies: list[TechDescription] = Field(description="List of Technogoies the company is developing")
    
    
