# Author: Alden Sahi
# Date: 07/29/2026
# Program Name: SummarizationLLM
#! Project Description: Builds a class that allows for LLM initalization, and
    # summary generation given a git commit

import requests
import json
from pydantic import BaseModel, Field
from typing import Dict, Union, Any
import time as t

class ContextWindowExceededError(Exception):
    def __init__(self, prompt_tokens: int, context_length: int):
        self.prompt_tokens = prompt_tokens          
        self.context_length = context_length
        super().__init__(f"Prompt is {prompt_tokens} tokens; context window is {context_length}")


class LocalLLM:

    # Constructor Definition
    def __init__(self, name: str):
        self.name = name
        print(f"\nInitalizing {self.name} Local LLM")
        
        # Docker Model Runner Listens on IPv4
        # A localhost request resolves to IPv6, this fails (Windows reports ~2s on RefusedConnectionError after multiple retries)
        # If that wasnt bad enough, requests tries the IPv6 (::1) request then the 127.0.0.1 sequentially causign the high latency
        self.base = f"http://127.0.0.1:12434/engines/llama.cpp/v1/"
        self.api = f"http://127.0.0.1:12434/engines/llama.cpp/v1/chat/completions"
        self.count_tokens_api = f"http://127.0.0.1:12434/anthropic/v1/messages/count_tokens"
        
        self.check_model()
        self.context_length = self.fetch_context_length()   # Does one call to LLM to extract context window size
        
        print(f"\t- Context window: {self.context_length} tokens.")

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


    def fetch_context_length(self) -> int:
        # Docker Model Runner doesn't expose llama.cpp's /props, so probe it instead: send a prompt
        # larger than any context window and read n_ctx from the "exceed_context_size_error" response.
        # The request is rejected after tokenization, so no inference runs (~5s, called once in __init__).
        data: dict[str, Any] = {
            "model": f"{self.name}",
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "hello " * 1_100_000}]     # ~1.1M tokens
        }
        response = requests.post(f"{self.api}", json=data, timeout=120)

        error: dict[str, Any] = {}
        try:
            error = response.json().get("error", {})
        except ValueError:
            pass
        if error.get("type") != "exceed_context_size_error" or "n_ctx" not in error:
            raise RuntimeError(
                f"Could not determine context length for '{self.name}' (HTTP {response.status_code}: {response.text[:300]})"
            )

        return int(error["n_ctx"])


    def get_token_length(self, data: dict[str, Any]) -> int:
        # Prompt tokens of a chat completions payload, chat-template tokens included (matches usage.prompt_tokens).
        # DMR's Anthropic-compatible count_tokens runs only the tokenizer (no inference). Anthropic format takes
        # system prompts as a top-level "system" field, not as messages.
        messages: list[dict[str, Any]] = data["messages"]
        count_data: dict[str, Any] = {
            "model": f"{self.name}",
            "messages": [m for m in messages if m["role"] != "system"]
        }
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        if system:
            count_data["system"] = system

        response = requests.post(f"{self.count_tokens_api}", json=count_data, timeout=30)
        response.raise_for_status()
        return int(response.json()["input_tokens"])


    def exceeds_context_window(self, messages: dict[str, Any]) -> None:
        """Raises ContextWindowError if the payload's prompt is too large for the model"""
        token_length: int = self.get_token_length(messages)
        if token_length > self.context_length:
            raise ContextWindowExceededError(token_length, self.context_length)

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
        
        # Assess Prompt Size compare to max size ( avoids a LLM call when we can if input is too larger quicker)
        self.exceeds_context_window(data)
        
        start_time = t.perf_counter()
        response = requests.post(f"{self.api}", json=data)
        runtime = t.perf_counter() - start_time        
        response.raise_for_status()
        body = response.json()
        
        # Runtime Analysis
        usage = body.get("usage", {})
        print(f"Processed query in {runtime:.2f}s ({usage.get('prompt_tokens')} prompt + "
            f"{usage.get('completion_tokens')} output tokens, "
            f"{usage.get('completion_tokens', 0) / runtime:.1f} tok/s)")

        choice = body["choices"][0]
        if choice["finish_reason"] == "length":
            raise RuntimeError(
                f"Output truncated at token limit (usage: {body.get('usage')})"
            )
            
        content = choice["message"]["content"]        
        return output.model_validate_json(content)




if __name__ == "__main__":
    agent = LocalLLM("docker.io/ai/gemma4:latest")
