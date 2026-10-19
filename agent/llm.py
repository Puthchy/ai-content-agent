"""Claude calls that return validated JSON matching a pydantic schema."""

import json
from typing import TypeVar

import anthropic
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class RefusedError(RuntimeError):
    pass


class LLM:
    def __init__(self, api_key: str, model: str, effort: str, system: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.effort = effort
        self.system = system

    def ask(self, prompt: str, schema: type[T]) -> T:
        response = self.client.beta.messages.create(
            model=self.model,
            max_tokens=16000,
            system=self.system,
            messages=[{"role": "user", "content": prompt}],
            output_config={
                "effort": self.effort,
                "format": {"type": "json_schema", "schema": schema.model_json_schema()},
            },
            # Retry on Anthropic's recommended model if a safety classifier declines.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            raise RefusedError(f"model declined: {response.stop_details}")
        if response.stop_reason == "max_tokens":
            raise RuntimeError("response hit max_tokens before finishing the JSON")
        text = next(b.text for b in response.content if b.type == "text")
        return schema.model_validate(json.loads(text))
