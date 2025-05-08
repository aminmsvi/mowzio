from dataclasses import dataclass

from app.config import settings


@dataclass
class LLmSettings:
    model: str
    base_url: str
    api_key: str


default_llm_settings = LLmSettings(
    model=settings.LLM_CLIENT_MODEL,
    api_key=settings.LLM_CLIENT_API_KEY,
    base_url=settings.LLM_CLIENT_BASE_URL,
)
