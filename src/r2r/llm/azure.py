"""
Azure OpenAI loader. Reads root .env. Uses deployment names.
Falls back to deterministic stubs when creds or network are disabled.
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import List
from dotenv import load_dotenv

# Load .env at workspace root
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"), override=False)

try:
    from openai import AzureOpenAI
except Exception:
    AzureOpenAI = None  # type: ignore

@dataclass
class AzureConfig:
    endpoint: str | None = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key: str | None = os.getenv("AZURE_OPENAI_API_KEY")
    api_version: str | None = os.getenv("AZURE_OPENAI_API_VERSION")
    chat_deployment: str | None = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")
    embed_deployment: str | None = os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT")
    allow_network: bool = os.getenv("R2R_ALLOW_NETWORK", "0") == "1"

_cfg = AzureConfig()

def _client():
    if not (_cfg.endpoint and _cfg.api_key and _cfg.api_version and AzureOpenAI):
        return None
    return AzureOpenAI(
        azure_endpoint=_cfg.endpoint,
        api_key=_cfg.api_key,
        api_version=_cfg.api_version,
    )

def chat(messages: list[dict], **kwargs) -> str:
    cli = _client()
    if cli and _cfg.allow_network and _cfg.chat_deployment:
        resp = cli.chat.completions.create(
            model=_cfg.chat_deployment,
            messages=messages,
            **kwargs,
        )
        return resp.choices[0].message.content or ""
    return "[stubbed-ai-response]"

def embed(texts: List[str], **kwargs) -> list[list[float]]:
    cli = _client()
    if cli and _cfg.allow_network and _cfg.embed_deployment:
        resp = cli.embeddings.create(model=_cfg.embed_deployment, input=texts, **kwargs)
        return [d.embedding for d in resp.data]
    return [[0.0] * 8 for _ in texts]
