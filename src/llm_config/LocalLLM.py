# Author: Alden Sahi
# Date: 07/29/2026
# Program Name: SummarizationLLM
#! Project Description: Builds a class that allows for LLM initalization, and
    # summary generation given a git commit

import requests
import json
from pydantic import BaseModel, Field
from typing import Dict, Union, Any

class LocalLLM:

    # Constructor Definition
    def __init__(self, name: str):
        self.name = name
        self.base = f"http://localhost:12434/engines/llama.cpp/v1/"
        self.api = f"http://localhost:12434/engines/llama.cpp/v1/chat/completions"
        self.check_model()

    def check_model(self):
        try:
            r = requests.get(f"{self.base}/models/", timeout=5)
            r.raise_for_status()
        
        except requests.ConnectionError as e:
            raise RuntimeError("Docker Model Runner not reachable on :12434. Is Docker running with TCP enabled?")
        
        available = {m["id"] for m in r.json().get("data", [])}
        if self.name not in available:
            error_msg = f"""
                    Model '{self.name}' not pulled. \n
                    Available models: {available} \n
                    Pull new model using: docker model pull MODEL_NAME
                    """
            raise RuntimeError(error_msg)
        

    def output_structured_format(self, system_prompt: str, user_prompt: str, output: type[BaseModel])-> BaseModel:
        schema = output.model_json_schema()
        data: dict[str, Any] = {
            "model": f"{self.name}",
            "messages": [
                {
                    "role": "system",
                    "content": f"{system_prompt}\n\nRespond with JSON matching this schema:\n{json.dumps(schema, indent=2)}"
                },
                {
                    "role": "user",
                    "content": f"{user_prompt}"
                }
            ],
            
            
            "response_format": {            
                "type": "json_schema",              # (llama.cpp) enables grammar based sampling ~ limits tokens the model can output 
                "json_schema": {
                    "name": "OutputFormat",
                    "schema": schema
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
        return output.model_validate_json(content)




if __name__ == "__main__":
    agent = LocalLLM("ai/qwen3.5:9B-UD-Q4_K_XL")
