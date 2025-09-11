from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field
import os


class Settings(BaseModel):
    # Policy and runtime
    ai_mode: Literal["off", "assist", "strict"] = Field(default="assist")
    data_path: Path = Field(default=Path("data"))
    out_path: Path = Field(default=Path("out"))
    period: str = Field(default="2025-08")
    prior: Optional[str] = Field(default=None)
    entity: str = Field(default="ALL")
    show_prompts: bool = Field(default=False)
    save_evidence: bool = Field(default=True)

    # AI providers / networking policy
    r2r_allow_network: bool = Field(default=True)

    # Azure OpenAI
    azure_openai_endpoint: Optional[str] = Field(default=None)
    azure_openai_api_key: Optional[str] = Field(default=None)
    azure_openai_api_version: Optional[str] = Field(default=None)
    azure_openai_chat_deployment: Optional[str] = Field(default=None)
    azure_openai_embeddings_deployment: Optional[str] = Field(default=None)

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)

    # Derived / internals
    repo_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    code_hash: str = Field(default="")

    @property
    def env_path(self) -> Path:
        return self.repo_root / ".env"


def load_settings_with_env(**overrides) -> Settings:
    """Load .env from the repository root ALWAYS, then create Settings.

    This does not rely on the current working directory. The repo root is computed
    relative to this file at runtime: src/r2r/config.py -> repo_root = parents[2].
    """
    repo_root = Path(__file__).resolve().parents[2]
    env_file = repo_root / ".env"
    # Always attempt to load .env from repo root. Do not override existing env vars.
    load_dotenv(dotenv_path=env_file, override=False)

    # Read environment variables with sensible defaults
    settings = Settings(
        ai_mode=os.getenv("R2R_AI_MODE", overrides.get("ai_mode", "assist")),
        data_path=Path(os.getenv("R2R_DATA_PATH", str(overrides.get("data_path", repo_root / "data")))),
        out_path=Path(os.getenv("R2R_OUT_PATH", str(overrides.get("out_path", repo_root / "out")))),
        period=os.getenv("R2R_PERIOD", overrides.get("period", "2025-08")),
        prior=os.getenv("R2R_PRIOR", overrides.get("prior")),
        entity=os.getenv("R2R_ENTITY", overrides.get("entity", "ALL")),
        show_prompts=_to_bool(os.getenv("R2R_SHOW_PROMPTS", str(overrides.get("show_prompts", False)))),
        save_evidence=_to_bool(os.getenv("R2R_SAVE_EVIDENCE", str(overrides.get("save_evidence", True)))),
        r2r_allow_network=_to_bool(os.getenv("R2R_ALLOW_NETWORK", str(overrides.get("r2r_allow_network", True)))),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_openai_chat_deployment=os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT") or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        azure_openai_embeddings_deployment=os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        repo_root=repo_root,
    )
    return settings


def _to_bool(v: str | bool | None) -> bool:
    if isinstance(v, bool):
        return v
    if v is None:
        return False
    return str(v).strip().lower() in {"1", "true", "yes", "y", "on"}
