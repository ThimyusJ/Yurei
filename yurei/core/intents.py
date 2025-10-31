import re
from typing import Optional, Dict

IP_CIDR_RE = re.compile(r"\b(?:(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?)\b")
HOSTNAME_RE = re.compile(r"\b([a-z0-9\-]+\.[a-z]{2,})\b", re.I)
PORTS_RE = re.compile(r"\b(?:ports?|p)\s*[:=]?\s*([\d,\-]+)\b", re.I)
RAW_PORTS_RE = re.compile(r"\b(\d{1,5}(?:-\d{1,5})?(?:,\d{1,5})*)\b")

FLAG_WORDS = {
    "verbose": ["verbose", "-v", "v"],
    "aggressive": ["aggressive", "-A", "aggr"],
    "udp": ["udp"],
    "ping": ["ping", "icmp"],
    "http": ["http", "web"],
    "smb": ["smb"],
    "vuln": ["vuln", "vulnerability"],
}

def _find_target(text: str) -> Optional[str]:
    m = IP_CIDR_RE.search(text)
    if m:
        return m.group(0)
    m = HOSTNAME_RE.search(text)
    if m:
        return m.group(0)
    return None

def _find_ports(text: str) -> Optional[str]:
    m = PORTS_RE.search(text)
    if m:
        return m.group(1)
    m_all = RAW_PORTS_RE.findall(text)
    for token in m_all:
        if "," in token or "-" in token or (token.isdigit() and 1 <= int(token) <= 65535):
            return token
    return None

def _find_flags(text: str) -> Dict[str, bool]:
    lower = text.lower()
    return {name: any(k.lower() in lower for k in keys) for name, keys in FLAG_WORDS.items()}

def parse_intent(user_input: str) -> Dict:
    text = (user_input or "").strip()
    lower = text.lower()
    intent = "unknown"
    if any(w in lower for w in ("nmap", "scan")):
        intent = "nmap_scan"
    if "udp" in lower:
        intent = "udp_scan"
    if any(w in lower for w in ("http", "web")):
        intent = "http_enum"
    if any(w in lower for w in ("smb", "ms17")):
        intent = "smb_enum"
    if any(w in lower for w in ("vuln", "vulnerability")):
        intent = "vuln_scan"
    if any(w in lower for w in ("ping", "host discovery", "-sn")):
        intent = "ping"

    slots = {
        "target": _find_target(text),
        "ports": _find_ports(text),
    }
    slots.update(_find_flags(text))
    slots["mode"] = "udp" if slots.get("udp") else "tcp"

    required = ["target"] if intent in ("nmap_scan", "udp_scan", "http_enum", "smb_enum", "vuln_scan", "ping") else []
    missing = [s for s in required if not slots.get(s)]
    return {"intent": intent, "slots": slots, "required": required, "missing": missing}
