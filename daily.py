#!/usr/bin/env python3
"""Daily Planner & Logger - Unified entry point."""
import sys
import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
import questionary
from questionary import Choice


def show_menu(console: Console) -> str:
    """Display main menu and get user choice.
    
    Args:
        console: Rich console
        
    Returns:
        User's choice as string
    """
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Daily Planner & Logger[/bold cyan]\n"
        "[dim]Your AI-powered productivity companion[/dim]",
        border_style="cyan"
    ))
    
    console.print("\n[bold green]Use arrow keys to navigate ↑↓, Enter to select[/bold green]\n")
    
    choices = [
        Choice("🌅 Plan my day (morning)", value="plan"),
        Choice("✅ Check tasks", value="check"),
        Choice("🌙 Summarize my day (evening)", value="summarize"),
        Choice("📊 View feedback", value="feedback"),
        Choice("─" * 40, disabled=True),
        Choice("❌ Exit", value="exit")
    ]
    
    result = questionary.select(
        "What would you like to do?",
        choices=choices,
        use_arrow_keys=True
    ).ask()
    
    return result if result else "exit"


def run_script(script_name: str, console: Console):
    """Run a script using subprocess.
    
    Args:
        script_name: Name of the script to run (e.g., 'plan.py')
        console: Rich console
    """
    script_path = Path(__file__).parent / script_name
    
    if not script_path.exists():
        console.print(f"[red]Error: {script_name} not found![/red]")
        return
    
    try:
        # Run the script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=False
        )
        
        if result.returncode != 0:
            console.print(f"\n[yellow]Script exited with code {result.returncode}[/yellow]")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error running {script_name}: {e}[/red]")


def main():
    """Main menu loop."""
    console = Console()
    
    while True:
        choice = show_menu(console)
        
        if choice == "plan":
            console.print("\n[dim]Starting morning planning...[/dim]\n")
            run_script("plan.py", console)
        
        elif choice == "check":
            console.print("\n[dim]Opening task checker...[/dim]\n")
            run_script("check.py", console)
        
        elif choice == "summarize":
            console.print("\n[dim]Starting evening summary...[/dim]\n")
            run_script("summarize.py", console)
        
        elif choice == "feedback":
            console.print("\n[dim]Opening feedback viewer...[/dim]\n")
            run_script("feedback.py", console)
        
        elif choice == "exit" or choice is None:
            console.print("\n[green]Have a great day! 👋[/green]\n")
            break
        
        # Pause before showing menu again
        if choice in ["plan", "check", "summarize", "feedback"]:
            console.print("\n[dim]Press Enter to return to menu...[/dim]")
            input()


if __name__ == "__main__":
    main()
