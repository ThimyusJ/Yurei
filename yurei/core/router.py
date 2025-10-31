from rich.console import Console
from .intents import parse_intent
from .dialog import DialogManager
from yurei.plugins import nmap_plugin

console = Console()
dm = DialogManager()

def route(intent_payload: dict, user_input: str, session_id: str = "local"):
    missing = intent_payload.get("missing", [])
    if missing:
        slot = missing[0]
        if slot == "target":
            dm.require_slot(session_id, intent_payload, "target", "Which target would you like to scan? (IP/CIDR/hostname)")
            return
        if slot == "ports":
            dm.require_slot(session_id, intent_payload, "ports", "Which ports or range? e.g. '22,80' or '1-1024'")
            return

    intent = intent_payload["intent"]
    slots = intent_payload["slots"]
    target = slots.get("target", "127.0.0.1")
    ports = slots.get("ports")

    if intent == "nmap_scan":
        if ports:
            nmap_plugin.run_scan(f"{target} -p {ports}")
        else:
            nmap_plugin.run_scan(target)
        if slots.get("verbose"):
            nmap_plugin.verbose_scan(target)
        return

    if intent == "udp_scan":
        nmap_plugin.udp_scan(f"{target} {ports or '1-1024'}")
        return

    if intent == "http_enum":
        nmap_plugin.http_enum(target)
        return

    if intent == "smb_enum":
        nmap_plugin.smb_enum(target)
        return

    if intent == "vuln_scan":
        nmap_plugin.vuln_script_scan(target)
        return

    if intent == "ping":
        nmap_plugin.host_discovery(target)
        return

    console.print(f"[yellow]Unknown intent:[/yellow] {intent}")


