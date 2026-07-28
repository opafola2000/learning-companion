import json
import logging

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings
from app.services.anthropic_client import AnthropicClient
from app.utils.json_parse import parse_llm_json

logger = logging.getLogger(__name__)


class BedrockClient:
    def __init__(self):
        settings = get_settings()
        session_kwargs = {"region_name": settings.aws_region}
        if settings.aws_access_key_id:
            session_kwargs["aws_access_key_id"] = settings.aws_access_key_id
            session_kwargs["aws_secret_access_key"] = settings.aws_secret_access_key
        session = boto3.Session(**session_kwargs)
        self.client = session.client("bedrock-runtime")
        self.sonnet_model = settings.bedrock_sonnet_model
        self.haiku_model = settings.bedrock_haiku_model
        self._anthropic: AnthropicClient | None = None
        if settings.anthropic_api_key:
            self._anthropic = AnthropicClient()

    def _invoke(self, model_id: str, system_prompt: str, user_message: str, max_tokens: int = 4096) -> str:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}],
        })
        response = self.client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

    def _invoke_with_fallback(
        self,
        tier: str,
        model_id: str,
        system_prompt: str,
        user_message: str,
        max_tokens: int,
    ) -> str:
        try:
            return self._invoke(model_id, system_prompt, user_message, max_tokens)
        except (ClientError, BotoCoreError) as exc:
            if not self._anthropic:
                raise
            logger.warning("Bedrock %s call failed (%s), falling back to Anthropic API", tier, exc)
            if tier == "sonnet":
                return self._anthropic.invoke_sonnet(system_prompt, user_message, max_tokens)
            return self._anthropic.invoke_haiku(system_prompt, user_message, max_tokens)

    def invoke_sonnet(self, system_prompt: str, user_message: str, max_tokens: int = 4096) -> str:
        return self._invoke_with_fallback("sonnet", self.sonnet_model, system_prompt, user_message, max_tokens)

    def invoke_haiku(self, system_prompt: str, user_message: str, max_tokens: int = 2048) -> str:
        return self._invoke_with_fallback("haiku", self.haiku_model, system_prompt, user_message, max_tokens)

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


_bedrock_client: BedrockClient | None = None


def get_bedrock_client() -> BedrockClient:
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient()
    return _bedrock_client
