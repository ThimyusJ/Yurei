import subprocess
import shutil
from rich.console import Console

console = Console()

def run_command(cmd: str):
    #Safely run a shell command and display the result
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            console.print(f"[cyan]{result.stdout}[/cyan]")
        if result.stderr:
            console.print(f"[red]{result.stderr}[/red]")
    except Exception as e:
        console.print(f"[red]Error executing command:[/red] {e}")


def check_dependencies():
    #Check for essential system tools and python packages.
    REQUIRED_TOOLS = ["nmap", "ping"]
    console.print("[bold cyan] Checking system dependencies...[/bold cyan]")

    for tool in REQUIRED_TOOLS:
        if shutil.which(tool):
            console.print(f"{tool} found.")
        else:
            console.print(f"{tool} missing. Install with sudo apt install {tool}")