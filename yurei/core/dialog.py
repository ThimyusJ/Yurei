from typing import Optional, Dict
from rich.console import Console
from .intents import _find_target, _find_ports

console = Console()

class DialogManager:
    def __init__(self):
        self._sessions = {}

    def require_slot(self, session_id: str, intent_payload: Dict, slot_name: str, prompt: str):
        self._sessions[session_id] = {"intent_payload": intent_payload, "pending_slot": slot_name}
        console.print(f"[cyan]{prompt}[/cyan]")

    def get_pending(self, session_id: str) -> Optional[Dict]:
        return self._sessions.get(session_id)

    def fill_slot(self, session_id: str, text: str) -> Optional[Dict]:
        state = self._sessions.get(session_id)
        if not state:
            return None
        payload = state["intent_payload"]
        slot = state["pending_slot"]
        if slot == "target":
            payload["slots"]["target"] = _find_target(text) or text.strip()
        elif slot == "ports":
            payload["slots"]["ports"] = _find_ports(text) or text.strip()
        payload["missing"] = [s for s in payload["required"] if not payload["slots"].get(s)]
        self._sessions.pop(session_id, None)
        return payload
