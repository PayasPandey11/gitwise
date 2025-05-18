"""Simple and efficient UI components for GitWise."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.box import ROUNDED
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text
from rich.padding import Padding

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
    
    # Show only first 20 lines to keep it concise, append ellipsis if longer.
    content = "\n".join(lines[:20])
    if len(lines) > 20:
        content += "\n..."
    
    console.print(Panel(content, title=title, box=ROUNDED))

def show_menu(options: list[tuple[str, str]]) -> None:
    """Show a simple numbered menu with clear separation."""
    # Add a separator line
    console.print("\n" + "─" * 50)
    
    # Show menu title
    console.print("\n[bold blue]What would you like to do?[/bold blue]")
    
    # Show options with numbers
    for i, (_, text) in enumerate(options, 1):
        console.print(f"[bold cyan]{i}[/bold cyan] {text}")
    
    # Add another separator
    console.print("\n" + "─" * 50)
    
    # Show prompt with clear formatting
    console.print("\n[bold yellow]Select an option[/bold yellow] [dim](press Enter for default)[/dim]")

def show_prompt(prompt: str, options: list[str] = None, default: str = None) -> None:
    """Show a formatted prompt for user input."""
    # Add a separator line
    console.print("\n" + "─" * 50)
    
    # Show prompt with clear formatting
    if options:
        console.print(f"\n[bold blue]{prompt}[/bold blue]")
        for i, option in enumerate(options, 1):
            console.print(f"[bold cyan]{i}[/bold cyan] {option}")
    else:
        if default:
            console.print(f"\n[bold yellow]{prompt}[/bold yellow] [dim](default: {default})[/dim]")
        else:
            console.print(f"\n[bold yellow]{prompt}[/bold yellow]")
    
    # Add another separator
    console.print("\n" + "─" * 50)

def show_error(message: str) -> None:
    """Show a simple error message."""
    console.print(f"\n[bold red]Error:[/bold red] {message}")

def show_success(message: str) -> None:
    """Show a simple success message."""
    console.print(f"\n[bold green]✓[/bold green] {message}")

def show_warning(message: str) -> None:
    """Show a simple warning message."""
    console.print(f"\n[bold yellow]![/bold yellow] {message}")

def show_section(title: str) -> None:
    """Show a section title with separators."""
    console.print("\n" + "─" * 50)
    console.print(f"\n[bold blue]{title}[/bold blue]")
    console.print("─" * 50) 