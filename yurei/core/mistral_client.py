# yurei/core/llm/mistral_client.py
import json
import os
import re
import requests
from typing import Dict, Any, List, Optional

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

# Hard JSON schema 
_SCHEMA = """\
Return ONLY this JSON (no prose), in one line:
{
  "intent": "nmap_scan|udp_scan|http_enum|smb_enum|vuln_scan|ping|unknown",
  "slots": {
    "target": string|null,
    "ports": string|null,
    "verbose": boolean,
    "aggressive": boolean,
    "udp": boolean,
    "http": boolean,
    "smb": boolean,
    "vuln": boolean,
    "save": boolean,
    "mode": "tcp"|"udp",
    "consent": boolean,
    "top": number|null
  },
  "required": string[],
  "missing": string[]
}"""

SYSTEM = f"""You convert natural language network requests into a strict JSON command for Yurei.
Rules:
- Do not execute anything. You only parse.
- If intrusive checks (vuln scan) are clearly authorized, set slots.consent=true, else false.
- If the intent requires a target and none is present, list "target" in "missing".
- Infer mode: "udp" only if user asked for UDP; else "tcp".
- If user says "top N", set slots.top=N.
- { _SCHEMA }
"""

def _strip_json(text: str) -> Optional[str]:
    """Extract the first JSON object from text, if the model wraps it."""
    m = re.search(r"\{.*\}", text, flags=re.S)
    return m.group(0) if m else None

class MistralClient:
    """
    Minimal client against Ollama's OpenAI-compatible /v1/chat/completions.
    """

    def __init__(self, url: str = OLLAMA_URL, model: str = OLLAMA_MODEL, timeout: int = 30):
        self.url = url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def infer(self, text: str) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": text},
            ],
            "temperature": 0.2,
            "stream": False,
        }
        r = requests.post(f"{self.url}/v1/chat/completions", json=payload, timeout=self.timeout)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]

        # Extract JSON if there’s extra text
        candidate = _strip_json(content) or content
        try:
            data = json.loads(candidate)
        except Exception:
            # Last-ditch: return unknown intent so rules can take over
            return {"intent": "unknown", "slots": {}, "required": [], "missing": []}

        # Basic sanity defaults
        data.setdefault("intent", "unknown")
        data.setdefault("slots", {})
        data.setdefault("required", [])
        data.setdefault("missing", [])
        s = data["slots"]
        for k, v in {
            "verbose": False, "aggressive": False, "udp": False, "http": False,
            "smb": False, "vuln": False, "save": False, "consent": False,
            "mode": "udp" if s.get("udp") else "tcp",
        }.items():
            s.setdefault(k, v)
        s.setdefault("top", None)
        s.setdefault("target", None)
        s.setdefault("ports", None)
        return data
