"""Simple and efficient UI components for GitWise."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.box import ROUNDED
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def show_spinner(description: str) -> Progress:
    """Show a simple spinner with description."""
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True
    )
    progress.add_task(description, total=None)
    return progress

def show_files_table(files: list[tuple[str, str]], title: str = "Changes") -> None:
    """Show a simple table of files with their status."""
    table = Table(
        show_header=True,
        header_style="bold",
        box=ROUNDED,
        title=title,
        title_style="bold"
    )
    table.add_column("Status", style="cyan", justify="center")
    table.add_column("File", style="green")
    
    for status, file in files:
        table.add_row(status, file)
    
    console.print(table)

def show_diff(diff: str, title: str = "Changes") -> None:
    """Show a simple diff with syntax highlighting."""
    if not diff:
        return
        
    lines = []
    for line in diff.splitlines():
        if line.startswith('+') and not line.startswith('+++'):
            lines.append(f"[green]{line}[/green]")
        elif line.startswith('-') and not line.startswith('---'):
            lines.append(f"[red]{line}[/red]")
        elif line.startswith('@@'):
            lines.append(f"[blue]{line}[/blue]")
        else:
            lines.append(line)
    
    # Show only first 20 lines to keep it concise
    content = "\n".join(lines[:20])
    if len(lines) > 20:
        content += "\n..."
    
    console.print(Panel(content, title=title, box=ROUNDED))

def show_menu(options: list[tuple[str, str]]) -> None:
    """Show a simple numbered menu."""
    console.print()
    for key, text in options:
        console.print(f"[cyan]{key}[/cyan] {text}")
    console.print()

def show_error(message: str) -> None:
    """Show a simple error message."""
    console.print(f"[red]Error: {message}[/red]")

def show_success(message: str) -> None:
    """Show a simple success message."""
    console.print(f"[green]✓ {message}[/green]")

def show_warning(message: str) -> None:
    """Show a simple warning message."""
    console.print(f"[yellow]! {message}[/yellow]") 