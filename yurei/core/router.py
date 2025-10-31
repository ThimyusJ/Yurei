# yurei/core/router.py
from rich.console import Console
from .dialog import DialogManager
from yurei.plugins import nmap_plugin

console = Console()
dm = DialogManager()

INTRUSIVE_INTENTS = {"vuln_scan"}  # you can add more later

def route(intent_payload: dict, user_input: str, session_id: str = "local"):
    # Ask for missing slots
    missing = intent_payload.get("missing", [])
    if missing:
        slot = missing[0]
        if slot == "target":
            dm.require_slot(session_id, intent_payload, "target", "Which target would you like to scan? (IP/CIDR/hostname)")
            return
        if slot == "ports":
            dm.require_slot(session_id, intent_payload, "ports", "Which ports or range? e.g. '22,80' or '1-1024'")
            return

    slots = intent_payload.get("slots", {})
    intent = intent_payload.get("intent")

    # Confirmation for intrusive actions
    needs_consent = (intent in INTRUSIVE_INTENTS) or bool(slots.get("vuln"))
    if needs_consent and not slots.get("consent", False):
        dm.require_confirmation(
            session_id,
            intent_payload,
            "This action will run intrusive vulnerability checks which may impact targets. "
            "Type [bold]YES[/bold] to proceed."
        )
        return

    # All set — hand off to plugin dispatcher (structured)
    nmap_plugin.handle_intent(intent_payload, user_input)




