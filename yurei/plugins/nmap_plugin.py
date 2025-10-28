from rich.console import Console
import subprocess
import shutil

console = Console()

def run_scan(user_input: str):
    #Perform a simple nmap scan based on input.
    if shutil.which("nmap") is None:
        console.print("[red]Error:[/red] nmap not found. Install it to use this plugin.")
        return
    
    target = "127.0.0.1" #For MVP use only!!!
    console.print(f"[cyan]Running nmap scan on {target}...[/cyan]")

    try:
        result = subprocess.run(["nmap", "-sV", target], capture_output=True, text=True)
        console.print(result.stdout)
    except Exception as e:
        console.print(f"[red]Error running nmap:[/red] {e}")