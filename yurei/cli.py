import typer
from rich.console import Console
from yurei.core import logger, router
from yurei.core import rules

app = typer.Typer(help="Yurei - modular CLI cyber assistant for Linux")
console = Console()
log = logger.get_logger()

@app.command()
def start():
    #Start Yurei in interactive mode.
    console.print("[bold cyan]Yurei online. Type 'exit' to quit.[/bold cyan]")
    while True:
        try:
            user_input = input("> ").strip()
            if user_input.lower() in ("exit", "quit"):
                console.print("[bold red]Shutting down...[/bold red]")
                break
            intent = rules.parse_intent(user_input)
            router.route(intent, user_input)
        except KeyboardInterrupt:
            console.print("\n[bold red]Interrupted by user.[/bold red]")
            break
        except Exception as e:
            log.error(f"Unexpected error: {e}")
            console.print(f"[red]Error:[/red] {e}")

@app.command()
def check_deps():
    #Check required tools and packages.
    from yurei.core.executor import check_dependencies
    check_dependencies()

@app.command()
def version():
    #Display Yurei version.
    console.print("[green] Yurei v0.1.0[/green]")

if __name__ == "__main__":
    app()