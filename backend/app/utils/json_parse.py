import json
import re


def parse_llm_json(raw: str) -> dict | list:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text.strip())

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    for opener, closer in [("{", "}"), ("[", "]")]:
        start = text.find(opener)
        end = text.rfind(closer)
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue

    raise json.JSONDecodeError("Could not parse LLM JSON response", text, 0)
