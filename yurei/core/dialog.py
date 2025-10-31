# yurei/core/dialog.py
from typing import Optional, Dict
from rich.console import Console
from .intents import _find_target, _find_ports

console = Console()

class DialogManager:
    def __init__(self):
        # session_id -> state
        # state: {"intent_payload": {...}, "pending_type": "slot"|"confirm", "pending_slot": "target"/"ports"/None, "prompt": "..."}
        self._sessions = {}

    # ----- slot follow-ups -----
    def require_slot(self, session_id: str, intent_payload: Dict, slot_name: str, prompt: str):
        self._sessions[session_id] = {
            "intent_payload": intent_payload,
            "pending_type": "slot",
            "pending_slot": slot_name,
            "prompt": prompt,
        }
        console.print(f"[cyan]{prompt}[/cyan]")

    # ----- confirmation follow-ups -----
    def require_confirmation(self, session_id: str, intent_payload: Dict, prompt: str):
        self._sessions[session_id] = {
            "intent_payload": intent_payload,
            "pending_type": "confirm",
            "pending_slot": None,
            "prompt": prompt,
        }
        console.print(f"[bold yellow]{prompt}[/bold yellow]")

    def get_pending(self, session_id: str) -> Optional[Dict]:
        return self._sessions.get(session_id)

    def answer(self, session_id: str, text: str) -> Optional[Dict]:
        state = self._sessions.get(session_id)
        if not state:
            return None
        payload = state["intent_payload"]
        pending_type = state["pending_type"]

        if pending_type == "slot":
            slot = state["pending_slot"]
            if slot == "target":
                payload["slots"]["target"] = _find_target(text) or text.strip()
            elif slot == "ports":
                payload["slots"]["ports"] = _find_ports(text) or text.strip()
            payload["missing"] = [s for s in payload["required"] if not payload["slots"].get(s)]
            self._sessions.pop(session_id, None)
            return payload

        if pending_type == "confirm":
            if text.strip().lower() in {"y","yes","ok","okay","confirm","i consent","proceed"}:
                payload["slots"]["consent"] = True
                self._sessions.pop(session_id, None)
                return payload
            else:
                console.print("[red]Cancelled.[/red] No action taken.")
                self._sessions.pop(session_id, None)
                return None


