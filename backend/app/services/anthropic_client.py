import json
import httpx
from app.config import get_settings
from app.utils.json_parse import parse_llm_json


class AnthropicClient:
    API_URL = "https://api.anthropic.com/v1/messages"

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.anthropic_api_key
        self.sonnet_model = settings.anthropic_sonnet_model
        self.haiku_model = settings.anthropic_haiku_model

    def _invoke(
        self,
        model: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 4096,
    ) -> str:
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        }
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        with httpx.Client(timeout=120.0) as client:
            response = client.post(self.API_URL, json=payload, headers=headers)
            if response.is_error:
                detail = response.text[:500]
                raise RuntimeError(
                    f"Anthropic API error ({response.status_code}) for model {model}: {detail}"
                )
            result = response.json()
        return result["content"][0]["text"]

    def invoke_sonnet(self, system_prompt: str, user_message: str, max_tokens: int = 4096) -> str:
        return self._invoke(self.sonnet_model, system_prompt, user_message, max_tokens)

    def invoke_haiku(self, system_prompt: str, user_message: str, max_tokens: int = 2048) -> str:
        return self._invoke(self.haiku_model, system_prompt, user_message, max_tokens)

    @staticmethod
    def _parse_json(raw: str) -> dict:
        result = parse_llm_json(raw)
        if isinstance(result, dict):
            return result
        return {"items": result}

    def invoke_sonnet_json(self, system_prompt: str, user_message: str, max_tokens: int = 4096) -> dict:
        full_system = system_prompt + "\n\nYou MUST respond with valid JSON only. No markdown, no code fences, no extra text."
        raw = self.invoke_sonnet(full_system, user_message, max_tokens)
        return self._parse_json(raw)

    def invoke_haiku_json(self, system_prompt: str, user_message: str, max_tokens: int = 2048) -> dict:
        full_system = system_prompt + "\n\nYou MUST respond with valid JSON only. No markdown, no code fences, no extra text."
        raw = self.invoke_haiku(full_system, user_message, max_tokens)
        return self._parse_json(raw)
