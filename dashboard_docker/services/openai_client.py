import os
import requests
from typing import List, Dict, Optional


OPENAI_API_BASE = os.environ.get("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_MODEL_DEFAULT = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")


class OpenAIConfigError(RuntimeError):
    pass


def _get_openai_api_key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise OpenAIConfigError("La variable d'environnement OPENAI_API_KEY n'est pas définie.")
    return key


def openai_chat_completion(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 900,
    timeout: int = 60,
) -> str:
    """
    Appelle OpenAI Chat Completions (REST) et renvoie le texte.
    - messages: [{role: system|user|assistant, content: "..."}]
    """
    api_key = _get_openai_api_key()
    use_model = model or OPENAI_MODEL_DEFAULT

    url = f"{OPENAI_API_BASE}/chat/completions"
    payload = {
        "model": use_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    r = requests.post(url, json=payload, headers=headers, timeout=timeout)
    r.raise_for_status()
    data = r.json()

    try:
        return (data["choices"][0]["message"]["content"] or "").strip()
    except Exception:
        # fallback best-effort
        return str(data)[:1000]
