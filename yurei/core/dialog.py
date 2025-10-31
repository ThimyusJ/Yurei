# yurei/router/dialog.py
from typing import Optional, Dict
from rich.console import Console
from .intents import _find_target, _find_ports

console = Console()

class DialogManager:
    def __init__(self):
        # session_id -> {"intent_payload": ..., "pending_slot": str}
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
        slots = payload.setdefault("slots", {})

        if slot == "target":
            slots["target"] = _find_target(text) or text.strip()

        elif slot == "ports":
            slots["ports"] = _find_ports(text) or text.strip()

        elif slot == "confirm":
            # Accept simple yes/no/ y / n
            ans = text.strip().lower()
            if ans in {"y", "yes"}:
                slots["__confirmation__"] = "yes"
            elif ans in {"n", "no"}:
                slots["__confirmation__"] = "no"
            else:
                # keep asking until a clear answer
                self._sessions[session_id] = state  # keep pending
                console.print("[yellow]Please answer 'yes' or 'no'.[/yellow]")
                return None

        # recompute missing
        payload["missing"] = [s for s in payload.get("required", []) if not slots.get(s)]
        # clear pending
        self._sessions.pop(session_id, None)
        return payload

