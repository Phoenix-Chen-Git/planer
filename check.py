#!/usr/bin/env python3
"""Check script - mark tasks as done from any day's plan with interactive menu."""
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.config_loader import load_config
from lib.storage import Storage
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
import questionary
from questionary import Choice


def get_available_plans(storage: Storage) -> list:
    """Get list of available plan dates.
    
    Returns:
        List of tuples (date_str, plan_path)
    """
    data_dir = storage.data_dir
    plan_files = sorted(data_dir.glob("*-plan.json"), reverse=True)
    
    plans = []
    for plan_file in plan_files:
        date_str = plan_file.stem.replace("-plan", "")
        plans.append((date_str, plan_file))
    
    return plans


def display_plan_selection(plans: list, console: Console) -> str:
    """Display available plans and let user select one.
    
    Args:
        plans: List of (date_str, plan_path) tuples
        console: Rich console
    
    Returns:
        Selected date string
    """
    if not plans:
        console.print("[red]No plans found in data directory.[/red]")
        return None
    
    # Create choices
    choices = []
    for date_str, _ in plans:
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = date_obj.strftime("%A")
            choices.append(Choice(f"{date_str} ({day_name})", value=date_str))
        except:
            choices.append(Choice(date_str, value=date_str))
    
    result = questionary.select(
        "Select a plan:",
        choices=choices
    ).ask()
    
    return result


def build_task_tree(jobs: list, completion_status: dict, depth: int = 0) -> list:
    """Build hierarchical task choices for questionary.
    
    Args:
        jobs: List of job dictionaries
        completion_status: Dict of job_name -> status ('done', 'quit', or None/pending)
        depth: Current depth level
    
    Returns:
        List of Choice objects
    """
    choices = []
    indent = "  " * depth
    
    for job in jobs:
        job_name = job.get('name') or job.get('task_name', 'Unknown')
        status = completion_status.get(job_name)
        
        # Three states: pending [ ], done [✓], quit [✗]
        if status == 'done' or status is True:  # Support legacy bool format
            checkbox = "[✓]"
        elif status == 'quit':
            checkbox = "[✗]"
        else:
            checkbox = "[ ]"
        
        choice_text = f"{indent}{checkbox} {job_name}"
        choices.append(Choice(choice_text, value=job_name))
        
        # Add sub-jobs
        sub_jobs = job.get('sub_jobs', [])
        if sub_jobs:
            sub_choices = build_task_tree(sub_jobs, completion_status, depth + 1)
            choices.extend(sub_choices)
    
    return choices


def mark_tasks_interactive(plan_data: dict, console: Console) -> dict:
    """Interactively mark tasks using arrow key navigation.
    
    Args:
        plan_data: Plan data dictionary
        console: Rich console
    
    Returns:
        Updated plan data with completion marks
    """
    if 'completion_status' not in plan_data:
        plan_data['completion_status'] = {}
    
    completion = plan_data['completion_status']
    jobs = plan_data.get('jobs', [])
    
    while True:
        # Build task tree
        choices = build_task_tree(jobs, completion)
        choices.append(Choice("─" * 40, disabled=True))
        choices.append(Choice("💾 Save and exit", value="__EXIT__"))
        
        # Show menu
        console.print("\n[bold green]Use arrow keys to navigate, Enter to cycle status[/bold green]")
        console.print("[dim]States: [ ] pending → [✓] done → [✗] quit → [ ] pending[/dim]")
        
        selected = questionary.select(
            "Select a task to toggle:",
            choices=choices,
            use_arrow_keys=True
        ).ask()
        
        if selected == "__EXIT__" or selected is None:
            break
        
        # Cycle through three states: pending -> done -> quit -> pending
        current_status = completion.get(selected)
        
        # Handle legacy boolean format
        if current_status is True:
            current_status = 'done'
        elif current_status is False:
            current_status = None
        
        if current_status is None:
            completion[selected] = 'done'
            console.print(f"[green]'{selected}' marked as done ✓[/green]")
        elif current_status == 'done':
            completion[selected] = 'quit'
            console.print(f"[red]'{selected}' marked as quit ✗[/red]")
        else:  # quit -> pending
            completion[selected] = None
            console.print(f"[yellow]'{selected}' marked as pending[/yellow]")
    
    plan_data['completion_status'] = completion
    plan_data['last_checked'] = datetime.now().isoformat()
    
    return plan_data


def count_all_tasks(jobs: list) -> int:
    """Recursively count all tasks including sub-jobs.
    
    Args:
        jobs: List of job dictionaries
        
    Returns:
        Total number of tasks
    """
    count = len(jobs)
    for job in jobs:
        sub_jobs = job.get('sub_jobs', [])
        if sub_jobs:
            count += count_all_tasks(sub_jobs)
    return count


def count_completed_tasks(jobs: list, completion_status: dict) -> int:
    """Recursively count completed tasks including sub-jobs.
    
    Args:
        jobs: List of job dictionaries
        completion_status: Dict of job_name -> status ('done', 'quit', or None)
        
    Returns:
        Number of completed tasks
    """
    count = 0
    for job in jobs:
        job_name = job.get('name') or job.get('task_name', 'Unknown')
        status = completion_status.get(job_name)
        # Count 'done' tasks (support legacy bool format)
        if status == 'done' or status is True:
            count += 1
        
        sub_jobs = job.get('sub_jobs', [])
        if sub_jobs:
            count += count_completed_tasks(sub_jobs, completion_status)
    
    return count


def count_quit_tasks(jobs: list, completion_status: dict) -> int:
    """Recursively count quit tasks including sub-jobs.
    
    Args:
        jobs: List of job dictionaries
        completion_status: Dict of job_name -> status ('done', 'quit', or None)
        
    Returns:
        Number of quit tasks
    """
    count = 0
    for job in jobs:
        job_name = job.get('name') or job.get('task_name', 'Unknown')
        if completion_status.get(job_name) == 'quit':
            count += 1
        
        sub_jobs = job.get('sub_jobs', [])
        if sub_jobs:
            count += count_quit_tasks(sub_jobs, completion_status)
    
    return count


def display_completion_summary(plan_data: dict, console: Console):
    """Display summary of completed tasks.
    
    Args:
        plan_data: Plan data dictionary
        console: Rich console
    """
    completion = plan_data.get('completion_status', {})
    jobs = plan_data.get('jobs', [])
    
    # Count all tasks including sub-jobs
    total = count_all_tasks(jobs)
    completed = count_completed_tasks(jobs, completion)
    quit_count = count_quit_tasks(jobs, completion)
    
    # Create summary table
    table = Table(title="Completion Summary", show_header=True, header_style="bold green")
    table.add_column("Task", style="cyan")
    table.add_column("Status", justify="center")
    
    for job in jobs:
        job_name = job['name']
        status_val = completion.get(job_name)
        # Handle legacy bool format
        if status_val == 'done' or status_val is True:
            status = "[green]✓[/green]"
        elif status_val == 'quit':
            status = "[red]✗[/red]"
        else:
            status = "[dim]○[/dim]"
        table.add_row(job_name, status)
    
    console.print("\n")
    console.print(table)
    
    # Calculate percentage based on resolved tasks (done + quit) vs total
    resolved = completed + quit_count
    percentage = completed * 100 // total if total > 0 else 0
    
    # Create visual progress bar with three sections
    bar_width = 30
    done_width = int(bar_width * completed / total) if total > 0 else 0
    quit_width = int(bar_width * quit_count / total) if total > 0 else 0
    pending_width = bar_width - done_width - quit_width
    
    # Color based on progress (completed tasks only)
    if percentage >= 80:
        bar_color = "green"
        emoji = "🎉"
    elif percentage >= 50:
        bar_color = "yellow"
        emoji = "💪"
    elif percentage >= 20:
        bar_color = "orange1"
        emoji = "🚀"
    else:
        bar_color = "cyan"
        emoji = "📋"
    
    progress_bar = f"[{bar_color}]{'█' * done_width}[/{bar_color}][red]{'█' * quit_width}[/red][dim]{'░' * pending_width}[/dim]"
    
    # Show stats
    pending = total - completed - quit_count
    stats = f"✓{completed} ✗{quit_count} ○{pending}"
    console.print(f"\n[bold]Progress:[/bold] {progress_bar} {stats} ({percentage}% done) {emoji}")


def main():
    """Main check workflow."""
    console = Console()
    
    # Print header
    console.print(Panel.fit(
        f"[bold green]Task Checker[/bold green]\n"
        f"[dim]Mark tasks as done with arrow keys[/dim]",
        border_style="green"
    ))
    
    try:
        # Initialize storage
        storage = Storage()
        
        # Get available plans
        plans = get_available_plans(storage)
        
        if not plans:
            console.print("\n[yellow]No plans found. Create a plan first with plan.py[/yellow]")
            return
        
        # Select plan
        console.print()
        selected_date = display_plan_selection(plans, console)
        
        if not selected_date:
            return
        
        # Load plan
        date_obj = datetime.strptime(selected_date, "%Y-%m-%d")
        plan_data = storage.load_plan(date_obj)
        
        if not plan_data:
            console.print(f"[red]Could not load plan for {selected_date}[/red]")
            return
        
        # Display plan content
        console.print(f"\n[bold cyan]Plan for {selected_date}:[/bold cyan]")
        console.print(Panel(
            Markdown(plan_data.get('plan_content', 'No content')),
            border_style="cyan"
        ))
        
        # Mark tasks interactively
        plan_data = mark_tasks_interactive(plan_data, console)
        
        # Save updated plan
        storage.save_plan(plan_data)
        
        # Display summary
        display_completion_summary(plan_data, console)
        
        console.print("\n[green]✓ Progress saved![/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
