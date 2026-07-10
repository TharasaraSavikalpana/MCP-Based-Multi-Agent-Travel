from typing import Optional

from agents.config import get_settings


def get_chat_model() -> Optional[object]:
    settings = get_settings()
    if not settings.has_openai_key:
        return None

    try:
        from langchain_openai import ChatOpenAI
    except Exception:
        return None

    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        temperature=0.3,
        streaming=True,
    )
