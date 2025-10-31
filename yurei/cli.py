# yurei/cli.py
import typer
from rich.console import Console
from yurei.core import logger
from yurei.router.intents import parse_intent
from yurei.router.router import route, dm

app = typer.Typer(help="Yurei — modular CLI cyber assistant for Linux")
console = Console()
log = logger.get_logger()
SESSION_ID = "local"

@app.command()
def start():
    console.print("[bold cyan]Yurei online. Type 'exit' to quit.[/bold cyan]")
    while True:
        try:
            user_input = input("> ").strip()
            if not user_input: continue
            if user_input.lower() in {"exit","quit"}:
                console.print("[bold red]Shutting down...[/bold red]"); break

            pending = dm.get_pending(SESSION_ID)
            if pending:
                updated = dm.answer(SESSION_ID, user_input)  # <— changed from fill_slot(...)
                if updated:
                    route(updated, user_input, SESSION_ID)
                continue

            payload = parse_intent(user_input)
            route(payload, user_input, SESSION_ID)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold red]Interrupted. Goodbye.[/bold red]"); break
        except Exception as e:
            log.error("Unexpected error", exc_info=True)
            console.print(f"[red]Error:[/red] {e}")

@app.command()
def run(command: str = typer.Argument(..., help="One-shot command, e.g. 'scan 192.168.1.0/24 top 100'")):
    payload = parse_intent(command)
    # fail fast if interactive follow-ups would be needed
    if payload.get("missing"):
        console.print(f"[yellow]Missing required info:[/yellow] {payload['missing']}. Try interactive: [cyan]yurei start[/cyan].")
        raise typer.Exit(code=2)
    if (payload["intent"] in {"vuln_scan"} or payload["slots"].get("vuln")) and not payload["slots"].get("consent"):
        console.print("[yellow]This command requires explicit consent. Add 'consent' or '--consent' to proceed, "
                      "or use interactive mode.[/yellow]")
        raise typer.Exit(code=3)
    route(payload, command, SESSION_ID)

@app.command()
def check_deps():
    from yurei.core.executor import check_dependencies
    check_dependencies()

@app.command()
def version():
    console.print("[green]Yurei v0.1.0[/green]")

if __name__ == "__main__":
    app()

