import typer
from rich.console import Console
from yurei.core import logger
from yurei.core.intents import parse_intent
from yurei.core.router import route, dm  # dm = shared DialogManager

app = typer.Typer(help="Yurei — modular CLI cyber assistant for Linux")
console = Console()
log = logger.get_logger()
SESSION_ID = "local"

@app.command()
def start():
    """
    Start Yurei in interactive mode.
    Supports follow-up questions (slot filling) via DialogManager.
    """
    console.print("[bold cyan]Yurei online. Type 'exit' to quit.[/bold cyan]")
    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                console.print("[bold red]Shutting down...[/bold red]")
                break

            # If waiting on a follow-up (e.g., target/ports), fill it first
            pending = dm.get_pending(SESSION_ID)
            if pending:
                updated = dm.fill_slot(SESSION_ID, user_input)
                if updated:
                    route(updated, user_input, SESSION_ID)
                continue

            # Fresh turn: parse → route (route will ask follow-ups if needed)
            payload = parse_intent(user_input)
            route(payload, user_input, SESSION_ID)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold red]Interrupted. Goodbye.[/bold red]")
            break
        except Exception as e:
            log.error("Unexpected error", exc_info=True)
            console.print(f"[red]Error:[/red] {e}")

@app.command()
def run(command: str = typer.Argument(..., help="One-shot command, e.g. 'scan 192.168.1.0/24 top 100'")):
    """
    Non-interactive one-shot: parses and routes a single command,
    no follow-up prompts (fails fast if info is missing).
    """
    payload = parse_intent(command)
    if payload.get("missing"):
        console.print(f"[yellow]Missing required info:[/yellow] {payload['missing']}. "
                      f"Try interactive mode: [cyan]yurei start[/cyan].")
        raise typer.Exit(code=2)
    route(payload, command, SESSION_ID)

@app.command()
def check_deps():
    """Check required tools and packages."""
    from yurei.core.executor import check_dependencies
    check_dependencies()

@app.command()
def version():
    """Display Yurei version."""
    console.print("[green]Yurei v0.1.0[/green]")

if __name__ == "__main__":
    app()
