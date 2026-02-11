import os
import time
from typing import Any, Dict, List, Optional

from google.genai import types

from .gemini_client import get_gemini_client
from .openai_client import openai_chat_completion, OpenAIConfigError


# ---- Retry / pacing ----
GEMINI_MAX_RETRIES = int(os.environ.get("GEMINI_MAX_RETRIES", "2"))
GEMINI_BACKOFF_BASE_SEC = float(os.environ.get("GEMINI_BACKOFF_BASE_SEC", "1.5"))

OPENAI_MAX_RETRIES = int(os.environ.get("OPENAI_MAX_RETRIES", "2"))
OPENAI_BACKOFF_BASE_SEC = float(os.environ.get("OPENAI_BACKOFF_BASE_SEC", "1.5"))


def _sleep_backoff(base: float, attempt_idx: int, cap: float = 12.0) -> None:
    wait = min(base * (2 ** attempt_idx), cap)
    time.sleep(wait)


def _extract_gemini_text(resp: Any) -> str:
    # La lib renvoie souvent resp.text, sinon candidates[].content.parts[].text
    text = (getattr(resp, "text", "") or "").strip()
    if text:
        return text

    candidates = getattr(resp, "candidates", None)
    if candidates:
        cand = candidates[0]
        content = getattr(cand, "content", None)
        parts = getattr(content, "parts", None) if content else None
        if parts:
            texts = []
            for p in parts:
                t = getattr(p, "text", None)
                if t:
                    texts.append(t)
            if texts:
                return "\n".join(texts).strip()

    return ""


def _is_gemini_quota_or_rate_error(err: Exception) -> bool:
    s = (str(err) or "").lower()
    # Messages typiques: 429, resource_exhausted, quota, rate limit, too many requests
    return (
        "429" in s
        or "resource_exhausted" in s
        or "quota" in s
        or "rate" in s and "limit" in s
        or "too many requests" in s
    )


def _is_transient(err: Exception) -> bool:
    s = (str(err) or "").lower()
    return any(k in s for k in ["timeout", "timed out", "temporar", "unavailable", "503", "504", "connection"])


def _gemini_contents_to_openai_messages(contents: List[types.Content]) -> List[Dict[str, str]]:
    """
    Convertit les contents Gemini (types.Content/Part) en messages OpenAI.
    - On met le 1er content (instruction) en role=system
    - role 'model' => 'assistant'
    - image parts sont ignorées (fallback texte)
    """
    messages: List[Dict[str, str]] = []
    for idx, c in enumerate(contents):
        role = getattr(c, "role", "user") or "user"
        parts = getattr(c, "parts", None) or []
        texts: List[str] = []
        for p in parts:
            t = getattr(p, "text", None)
            if t:
                texts.append(t)

        if not texts:
            # image-only => on met un placeholder si c'est le dernier message user
            continue

        content_text = "\n".join(texts).strip()
        if not content_text:
            continue

        if idx == 0:
            messages.append({"role": "system", "content": content_text})
            continue

        if role == "model":
            oa_role = "assistant"
        elif role == "user":
            oa_role = "user"
        else:
            oa_role = "user"

        messages.append({"role": oa_role, "content": content_text})

    return messages


def _call_gemini(gemini_model: str, contents: List[types.Content]) -> str:
    client = get_gemini_client()
    resp = client.models.generate_content(model=gemini_model, contents=contents)
    return _extract_gemini_text(resp)


def _call_openai(openai_model: str, contents: List[types.Content]) -> str:
    messages = _gemini_contents_to_openai_messages(contents)
    # Si aucun message, on évite un appel inutile
    if not messages:
        return ""
    return openai_chat_completion(messages=messages, model=openai_model)


def generate_text(
    contents: List[types.Content],
    gemini_model: str,
    openai_model: Optional[str] = None,
) -> str:
    """
    Routeur Multi-LLM:
    1) Tente Gemini (avec petits retries + backoff)
    2) Si quota/rate/erreur transitoire => fallback OpenAI (avec retries)
    3) Si OpenAI non configuré => message dégradé
    """
    # ---- Gemini first ----
    last_err: Optional[Exception] = None
    for i in range(max(GEMINI_MAX_RETRIES, 1)):
        try:
            txt = _call_gemini(gemini_model, contents)
            if txt:
                return txt
            # si réponse vide, on considère erreur transitoire
            raise RuntimeError("Gemini: empty response")
        except Exception as e:
            last_err = e
            if _is_gemini_quota_or_rate_error(e) or _is_transient(e):
                # backoff puis on retente (petit), sinon fallback
                if i < GEMINI_MAX_RETRIES - 1:
                    _sleep_backoff(GEMINI_BACKOFF_BASE_SEC, i)
                    continue
                break
            # erreur non transitoire => on ne retry pas
            break

    # ---- Fallback OpenAI ----
    use_openai_model = openai_model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    for i in range(max(OPENAI_MAX_RETRIES, 1)):
        try:
            txt = _call_openai(use_openai_model, contents)
            if txt:
                return txt
            raise RuntimeError("OpenAI: empty response")
        except OpenAIConfigError:
            # Pas de clé, on ne peut pas fallback
            break
        except Exception as e:
            last_err = e
            if i < OPENAI_MAX_RETRIES - 1:
                _sleep_backoff(OPENAI_BACKOFF_BASE_SEC, i)
                continue
            break

    # ---- Degraded ----
    # On reste simple, pas de détails techniques.
    return "Je suis temporairement limité (quota ou connexion). Réessaie dans 1–2 minutes."
