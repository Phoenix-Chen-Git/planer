#!/usr/bin/env python3
"""Daily Planner & Logger - Unified entry point with enhanced UI."""
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.storage import Storage
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import questionary
from questionary import Choice


def display_dashboard(storage: Storage, console: Console):
    """Display enhanced dashboard with stats and streak.
    
    Args:
        storage: Storage instance
        console: Rich console
    """
    now = datetime.now()
    
    # Date and time formatting
    date_str = now.strftime("%A, %B %d, %Y")
    time_str = now.strftime("%I:%M %p")
    
    # Get today's stats
    stats = storage.get_today_stats()
    total = stats['total']
    completed = stats['completed']
    quit_count = stats['quit']
    pending = stats['pending']
    
    # Calculate streak
    streak = storage.calculate_streak()
    
    # Build header content
    header_lines = []
    header_lines.append("[bold cyan]📅 Daily Planner & Logger[/bold cyan]")
    header_lines.append("[dim]─────────────────────────────────────────[/dim]")
    header_lines.append(f"[white]🗓️  {date_str}  •  {time_str}[/white]")
    
    # Stats line
    if total > 0:
        percentage = completed * 100 // total
        
        # Create mini progress bar
        bar_width = 15
        filled = int(bar_width * completed / total) if total > 0 else 0
        empty = bar_width - filled
        
        if percentage >= 80:
            bar_color = "green"
        elif percentage >= 50:
            bar_color = "yellow"
        else:
            bar_color = "cyan"
        
        mini_bar = f"[{bar_color}]{'█' * filled}[/{bar_color}][dim]{'░' * empty}[/dim]"
        stats_text = f"[white]📊 Today: {mini_bar} {completed}/{total} done[/white]"
        
        if quit_count > 0:
            stats_text += f" [dim]({quit_count} quit)[/dim]"
        
        header_lines.append(stats_text)
    else:
        header_lines.append("[dim]📊 No plan yet for today[/dim]")
    
    # Streak line
    if streak > 0:
        streak_emoji = "🔥" if streak >= 3 else "⭐"
        streak_text = f"[bold yellow]{streak_emoji} {streak}-day streak![/bold yellow]"
        if streak >= 7:
            streak_text = f"[bold green]🔥 {streak}-day streak! Amazing![/bold green]"
        elif streak >= 30:
            streak_text = f"[bold magenta]🏆 {streak}-day streak! Legend![/bold magenta]"
        header_lines.append(streak_text)
    
    # Create the panel
    console.print("\n")
    console.print(Panel(
        "\n".join(header_lines),
        border_style="cyan",
        padding=(0, 2)
    ))


def show_menu(console: Console) -> str:
    """Display main menu and get user choice.
    
    Args:
        console: Rich console
        
    Returns:
        User's choice as string
    """
    console.print("\n[bold]Use arrow keys ↑↓ to navigate, Enter to select[/bold]\n")
    
    choices = [
        Choice("🌅 Plan my day", value="plan"),
        Choice("✅ Check tasks", value="check"),
        Choice("🗂️ Plan by hierarchy", value="hierarchy"),
        Choice("─" * 35, disabled=True),
        Choice("🌙 Summarize my day", value="summarize"),
        Choice("📊 View feedback", value="feedback"),
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
    storage = Storage()
    
    while True:
        # Show enhanced dashboard
        display_dashboard(storage, console)
        
        # Show menu
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
        
        elif choice == "hierarchy":
            console.print("\n[dim]Opening hierarchy planner...[/dim]\n")
            run_script("hierarchy.py", console)
        
        elif choice == "exit" or choice is None:
            console.print("\n[bold green]Have a great day! 👋[/bold green]\n")
            break
        
        # Pause before showing menu again
        if choice in ["plan", "check", "summarize", "feedback", "hierarchy"]:
            console.print("\n[dim]Press Enter to return to menu...[/dim]")
            input()


if __name__ == "__main__":
    main()

