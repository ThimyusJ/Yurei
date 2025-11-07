# yurei/core/intent_engine.py
from typing import Optional, Dict, Any
import re
from yurei.core import intents as rules

TOP_RE = re.compile(r"\btop\s+(\d{1,5})\b", re.I)

class IntentEngine:
    def __init__(self, nlp: Optional[object] = None, use_llm_first: bool = False):
        self.nlp = nlp
        self.use_llm_first = use_llm_first

    def parse(self, text: str) -> Dict[str, Any]:
        if not self.use_llm_first:
            p = rules.parse_intent(text)
            self._maybe_infer_top(text, p)
            if p["intent"] != "unknown" and not p.get("missing"):
                return p
            if self.nlp:
                return self._nlp_parse(text, fallback=p)
            return p
        if self.nlp:
            return self._nlp_parse(text, fallback=rules.parse_intent(text))
        return rules.parse_intent(text)

    def _maybe_infer_top(self, text: str, payload: Dict[str, Any]) -> None:
        m = TOP_RE.search(text or "")
        if m:
            try:
                n = int(m.group(1))
                if n > 0:
                    payload.setdefault("slots", {})["top"] = n
            except ValueError:
                pass

    def _merge_payloads(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        out = dict(base)
        for k in ("intent", "required", "missing"):
            if k in override and override[k] is not None:
                out[k] = override[k]
        out_slots = dict(base.get("slots", {}))
        for sk, sv in (override.get("slots") or {}).items():
            out_slots[sk] = sv
        out["slots"] = out_slots
        out["slots"].setdefault("consent", False)
        out["slots"].setdefault("mode", "udp" if out["slots"].get("udp") else "tcp")
        if "required" in out:
            out["missing"] = [s for s in out.get("required", []) if not out["slots"].get(s)]
        return out

    def _nlp_parse(self, text: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
        try:
            llm = self.nlp.infer(text) if self.nlp else {}
            if not isinstance(llm, dict):
                llm = {}
        except Exception:
            llm = {}
        rules_pass = rules.parse_intent(text)
        self._maybe_infer_top(text, rules_pass)
        return self._merge_payloads(fallback or rules_pass, llm)
