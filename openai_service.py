import json
from typing import Any, Dict
from openai import OpenAI
from config import OPENAI_API_KEY, OPENAI_MODEL


if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing. Add it in your .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)


def _extract_text_from_response(response: Any) -> str:
    """
    Supports common OpenAI Python SDK response patterns.
    """
    # Newer SDKs often expose output_text
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text

    # Fallback traversal
    try:
        parts = []
        for item in response.output:
            if getattr(item, "type", None) == "message":
                for content in item.content:
                    if getattr(content, "type", None) in {"output_text", "text"}:
                        parts.append(content.text)
        if parts:
            return "\n".join(parts)
    except Exception:
        pass

    # Last fallback
    return str(response)


def generate_json(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """
    Uses the Responses API and asks for JSON.
    """
    response = client.responses.create(
        model=OPENAI_MODEL,
        input=[
            {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
        ],
    )

    text = _extract_text_from_response(response).strip()

    # Sometimes models wrap JSON in markdown fences
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()

    return json.loads(text)