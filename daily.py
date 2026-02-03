#!/usr/bin/env python3
"""Daily Planner & Logger - Unified entry point with enhanced UI."""
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.storage import Storage
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt
import questionary
from questionary import Choice

# Import calendar and goals functions
from calendar_view import (
    get_contribution_data,
    get_intensity_level,
    get_block_style,
    load_goals,
    display_goals,
    get_priority_emoji,
    get_stage_info
)


def display_mini_calendar(storage: Storage, console: Console, weeks: int = 16):
    """Display a compact contribution calendar.
    
    Args:
        storage: Storage instance
        console: Rich console
        weeks: Number of weeks to show (default 16 for ~4 months)
    """
    contributions = get_contribution_data(storage, weeks)
    
    # Get date range
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks)
    
    # Align to Sunday (start of week)
    start_date -= timedelta(days=start_date.weekday() + 1)
    if start_date.weekday() != 6:
        start_date -= timedelta(days=(start_date.weekday() + 1) % 7)
    
    # Calculate stats
    total_completed = sum(d['completed'] for d in contributions.values())
    active_days = sum(1 for d in contributions.values() if d['completed'] > 0)
    
    # Build calendar rows
    calendar_lines = []
    
    # Month labels header
    prev_month = -1
    month_positions = []
    
    for week in range(weeks):
        week_start = start_date + timedelta(weeks=week)
        if week_start.month != prev_month:
            month_name = week_start.strftime("%b")
            month_positions.append((week, month_name))
            prev_month = week_start.month
    
    # Create month header line
    month_line = ["    "]
    last_pos = 0
    for pos, month_name in month_positions:
        spaces_needed = pos - last_pos
        month_line.append(" " * (spaces_needed * 2))
        month_line.append(month_name)
        last_pos = pos + len(month_name) // 2
    
    calendar_lines.append(Text("".join(month_line), style="dim"))
    
    # Build each day row (7 rows for each day of week)
    day_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for day_idx in range(7):
        row = Text()
        
        # Day label (only show Mon, Wed, Fri)
        if day_idx in [1, 3, 5]:
            row.append(f"{day_labels[day_idx][0]} ", style="dim")
        else:
            row.append("  ")
        
        # Add each week's cell for this day
        for week in range(weeks):
            cell_date = start_date + timedelta(weeks=week, days=day_idx)
            date_str = cell_date.strftime("%Y-%m-%d")
            
            if date_str in contributions:
                data = contributions[date_str]
                intensity = get_intensity_level(data['completed'], data['total'])
                char, style = get_block_style(intensity, data['has_plan'])
                
                # Special styling for today
                if cell_date.date() == datetime.now().date():
                    row.append("◉", style="bold cyan")
                elif cell_date > datetime.now():
                    row.append(" ")
                else:
                    row.append(char, style=style)
            else:
                row.append(" ")
            
            row.append(" ")
        
        calendar_lines.append(row)
    
    # Legend and stats on same line
    legend = Text("\n    Less ")
    legend.append("□", style="dim")
    legend.append(" ")
    legend.append("▪", style="green4")
    legend.append(" ")
    legend.append("▪", style="green1")
    legend.append(" More  ")
    legend.append("◉", style="bold cyan")
    legend.append(" Today", style="dim")
    calendar_lines.append(legend)
    
    stats = Text(f"    📊 {total_completed} tasks • {active_days} active days")
    stats.stylize("dim")
    calendar_lines.append(stats)
    
    content = Text("\n").join(calendar_lines)
    
    console.print(Panel(
        content,
        title="[bold cyan]📅 Recent Activity[/bold cyan]",
        subtitle=f"[dim]{start_date.strftime('%b')} - {end_date.strftime('%b %Y')}[/dim]",
        border_style="cyan",
        padding=(0, 1)
    ))


def display_upcoming_tasks(storage: Storage, console: Console, config: Any):
    """Display upcoming tasks panel.

    Args:
        storage: Storage instance
        console: Rich console
        config: Config loader instance
    """
    # Get number of days from config
    preferences = config.get_preferences()
    days = preferences.get('upcoming_days', 7)

    upcoming = storage.get_upcoming_tasks(days=days)

    if not upcoming:
        console.print(Panel(
            "[dim]No upcoming tasks scheduled.[/dim]",
            title="[bold cyan]📅 Upcoming Tasks[/bold cyan]",
            border_style="cyan",
            padding=(0, 1)
        ))
        return

    # Group by date
    from collections import defaultdict
    by_date = defaultdict(list)
    for task in upcoming:
        by_date[task['date_str']].append(task)

    # Build display
    lines = []
    today = datetime.now().date()

    for date_str in sorted(by_date.keys()):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Format date label
        days_away = (date_obj - today).days
        if days_away == 1:
            date_label = "Tomorrow"
        elif days_away <= 7:
            date_label = date_obj.strftime("%a, %b %d")
        else:
            date_label = date_obj.strftime("%b %d")

        lines.append(f"[bold cyan]{date_label}[/bold cyan]")

        # Show tasks for this date
        for task in by_date[date_str]:
            indent = "  " if not task['is_subtask'] else "    "
            job_name = task['job_name']
            desc = task['task_description']

            # Truncate long descriptions
            if len(desc) > 50:
                desc = desc[:47] + "..."

            lines.append(f"{indent}• {job_name}: {desc}")

        lines.append("")  # Blank line between dates

    content = "\n".join(lines).rstrip()

    console.print(Panel(
        content,
        title=f"[bold cyan]📅 Upcoming Tasks (Next {days} Days)[/bold cyan]",
        border_style="cyan",
        padding=(0, 1)
    ))


def display_goals_compact(console: Console):
    """Display compact goals panel for main UI with stages.
    
    Args:
        console: Rich console
    """
    goals_data = load_goals()
    active_goals = [g for g in goals_data.get("goals", []) if g.get("status") == "active"]
    
    if not active_goals:
        console.print(Panel(
            "[dim]No goals set. Use 🎯 Manage goals to add some![/dim]",
            title="[bold cyan]🎯 Goals[/bold cyan]",
            border_style="cyan",
            padding=(0, 1)
        ))
        return
    
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    active_goals.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))
    
    # Show top 5 goals with stages
    goals_text = []
    for goal in active_goals[:5]:
        progress = goal.get("progress", 0)
        stage_name, stage_emoji, stage_color = get_stage_info(progress)
        
        bar_width = 6
        filled = int(bar_width * progress / 100)
        empty = bar_width - filled
        
        priority = get_priority_emoji(goal.get("priority", "low"))
        bar = f"[{stage_color}]{'█' * filled}[/{stage_color}][dim]{'░' * empty}[/dim]"
        goals_text.append(f"  {priority} {goal['name'][:20]:20} [{stage_color}]{stage_emoji}[/{stage_color}] {bar} {progress}%")
    
    if len(active_goals) > 5:
        goals_text.append(f"  [dim]... and {len(active_goals) - 5} more[/dim]")
    
    console.print(Panel(
        "\n".join(goals_text),
        title="[bold cyan]🎯 Goals[/bold cyan]",
        border_style="cyan",
        padding=(0, 1)
    ))


def display_dashboard(storage: Storage, console: Console):
    """Display enhanced dashboard with calendar and goals.
    
    Args:
        storage: Storage instance
        console: Rich console
    """
    console.clear()
    now = datetime.now()
    
    # Date and time formatting
    date_str = now.strftime("%A, %B %d, %Y")
    time_str = now.strftime("%I:%M %p")
    
    # Get today's stats
    stats = storage.get_today_stats()
    total = stats['total']
    completed = stats['completed']
    quit_count = stats['quit']
    
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
    
    # Print header
    console.print("\n")
    console.print(Panel(
        "\n".join(header_lines),
        border_style="cyan",
        padding=(0, 2)
    ))
    
    # Display mini calendar
    display_mini_calendar(storage, console, weeks=16)

    # Display upcoming tasks
    from lib.config_loader import load_config
    config = load_config()
    display_upcoming_tasks(storage, console, config)

    # Display goals
    display_goals_compact(console)


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
        Choice("📝 Add future task", value="future_task"),
        Choice("─" * 35, disabled=True),
        Choice("🌙 Summarize my day", value="summarize"),
        Choice("📊 View feedback", value="feedback"),
        Choice("📅 Full calendar view", value="calendar"),
        Choice("🎯 Manage goals", value="goals"),
        Choice("❌ Exit", value="exit")
    ]
    
    result = questionary.select(
        "What would you like to do?",
        choices=choices,
        use_arrow_keys=True
    ).ask()
    
    return result if result else "exit"


def add_future_task(storage: Storage, console: Console):
    """Add a task for a future date.

    Args:
        storage: Storage instance
        console: Rich console
    """
    console.print("\n[bold cyan]📝 Add Future Task[/bold cyan]\n")

    # Select date
    console.print("[dim]Select a date for this task:[/dim]")
    today = datetime.now()

    date_choices = []
    for i in range(1, 15):  # Next 14 days
        future_date = today + timedelta(days=i)
        label = future_date.strftime("%a, %b %d, %Y")
        if i == 1:
            label = f"Tomorrow ({future_date.strftime('%b %d')})"
        date_choices.append(Choice(label, value=future_date))

    date_choices.append(Choice("❌ Cancel", value=None))

    selected_date = questionary.select(
        "Choose date:",
        choices=date_choices,
        use_arrow_keys=True
    ).ask()

    if not selected_date:
        return

    # Load or create plan for that date
    plan_data = storage.load_plan(selected_date)

    if not plan_data:
        # Create new plan structure
        plan_data = {
            'date': selected_date.isoformat(),
            'jobs': [],
            'plan_content': '',
            'refinement_history': [],
            'completion_status': {}
        }

    # Get job category
    from lib.config_loader import load_config
    config = load_config()
    daily_jobs = config.get_daily_jobs()

    job_choices = [Choice(job['name'], value=job) for job in daily_jobs]
    job_choices.append(Choice("❌ Cancel", value=None))

    selected_job = questionary.select(
        "Select job category:",
        choices=job_choices,
        use_arrow_keys=True
    ).ask()

    if not selected_job:
        return

    # Get task description
    task_desc = Prompt.ask("[cyan]Task description[/cyan]")

    if not task_desc.strip():
        console.print("[yellow]No task description provided.[/yellow]")
        return

    # Add to plan
    job_entry = {
        'name': selected_job['name'],
        'description': selected_job['description'],
        'user_input': task_desc.strip(),
        'sub_jobs': [],
        'chat_notes': []
    }

    plan_data['jobs'].append(job_entry)

    # Update plan content (simple format)
    if not plan_data['plan_content']:
        plan_data['plan_content'] = f"# Plan for {selected_date.strftime('%Y-%m-%d')}\n\n"

    plan_data['plan_content'] += f"## {selected_job['name']}\n- [ ] {task_desc}\n\n"

    # Save plan
    storage.save_plan(plan_data)

    console.print(f"\n[green]✅ Task added to {selected_date.strftime('%A, %B %d')}![/green]")


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
        # Show enhanced dashboard with calendar and goals
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
        
        elif choice == "calendar":
            console.print("\n[dim]Opening contribution calendar...[/dim]\n")
            run_script("calendar_view.py", console)
        
        elif choice == "goals":
            # Import and run goals management
            from calendar_view import manage_goals
            manage_goals(console)

        elif choice == "future_task":
            add_future_task(storage, console)
            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()

        elif choice == "exit" or choice is None:
            console.print("\n[bold green]Have a great day! 👋[/bold green]\n")
            break
        
        # Pause before showing menu again
        if choice in ["plan", "check", "summarize", "feedback", "calendar"]:
            console.print("\n[dim]Press Enter to return to menu...[/dim]")
            input()


if __name__ == "__main__":
    main()
