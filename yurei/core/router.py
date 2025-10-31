from rich.console import Console
from yurei.core import executor
from yurei.plugins import nmap_plugin

console = Console()

def route(intent: str, user_input: str):
    #Route user input to the appropriate action or plugin
    if intent == "nmap_scan":
        nmap_plugin.run_scan(user_input)
        nmap_plugin.verbose_scan(user_input)
    elif intent == "udp_scan":
        nmap_plugin.udp_scan(user_input)
    elif intent == "ping":
        executor.run_command("ping -c 4 8.8.8.8")
    else:
        console.print(f"[bold yellow]Unknown intent:[/bold yellow] {intent}")