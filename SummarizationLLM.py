# Author: Alden Sahi
# Date: 07/29/2026
# Program Name: SummarizationLLM
#! Project Description: Builds a class that allows for LLM initalization, and 
    # summary generation given a git commit

import requests
import json
from pydantic import BaseModel, Field


class OutputFormat(BaseModel):
    project_id: str = Field(description="Parent folder name of the project")
    libraries: list[str] = Field(description="Third-party libraries imported/used in the code")
    data_structures: list[str] = Field(description="Data structures utilized (e.g. list, hash map, tree)")
    bigo_time_complexity: str = Field(description="Big O time complexity of the core algorithm")
    bigo_space_complexity: str = Field(description="Big O space complexity of the core algorithm")
    result: str = Field(description="Explanation of how this improved the existing solution, or the outcome if newly written")

 

class SummarizationLLM:

    # Constructor Definition
    def __init__(self, name: str):
        self.name = name
        self.api = f"http://localhost:12434/engines/llama.cpp/v1/chat/compeletions"
        self.system_prompt = ""
        
        self.prompt =  """
            You are a helpful assisant tasked to extract important values from this code including,
            a project_id (parent folder name), libraries, data structures and algorithms utilized. Along with big O space and time complexity along with a result 
            string that explains How did it improve the current or if new what did this result in.
        """
        self.output_format = OutputFormat



    def print_output_format(self)->dict:
        """Returns output criteria for the SummarizationLLM"""
        schema_dict = self.output_format.model_json_schema()
        print(json.dumps(schema_dict, indent=2))


    def summarize(self, prompt: str = "Please write 500 words about the fall of Rome"):
        data = {
            "model": f"{self.name}",
            "messages": [
                {
                    "role": "system", 
                    "content": self.system_prompt
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
                    "schema": OutputFormat.model_json_schema()
                }
            }
        }
        response = requests.post(f"{self.api}", json=data)
        response.raise_for_status()
        return response.json()

agent = SummarizationLLM("ai/qwen3.5:9B-UD-Q4_K_XL")
agent.print_output_format()