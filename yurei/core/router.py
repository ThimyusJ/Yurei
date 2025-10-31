# yurei/core/router.py
from rich.console import Console
from .intents import parse_intent
from .dialog import DialogManager
from yurei.plugins import nmap_plugin

console = Console()
dm = DialogManager()

def _needs_confirmation(intent_payload: dict) -> bool:
    """
    Decide if we must ask for an explicit confirmation before running.
    Currently: vuln scans or aggressive scans.
    """
    intent = intent_payload.get("intent", "")
    slots = intent_payload.get("slots", {}) or {}
    return (
        intent in {"vuln_scan"}              # explicit vuln scan
        or bool(slots.get("vuln"))           # user hinted 'vuln'
        or bool(slots.get("aggressive"))     # -A style scans
    )

def route(intent_payload: dict, user_input: str, session_id: str = "local"):
    """
    Route the parsed payload. If required slots are missing, ask for them.
    If intrusive, ask for confirmation. Otherwise, call the plugin dispatcher.
    """
    # 1) Ask for any missing required slots
    missing = intent_payload.get("missing", [])
    if missing:
        slot = missing[0]
        if slot == "target":
            dm.require_slot(session_id, intent_payload, "target",
                            "Which target would you like to scan? (IP/C



