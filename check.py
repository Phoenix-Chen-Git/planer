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
        completion_status: Dict of job_name -> bool
        depth: Current depth level
    
    Returns:
        List of Choice objects
    """
    choices = []
    indent = "  " * depth
    
    for job in jobs:
        job_name = job.get('name') or job.get('task_name', 'Unknown')
        is_done = completion_status.get(job_name, False)
        checkbox = "[✓]" if is_done else "[ ]"
        
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
        choices.append(Choice("✓ Done - Save and exit", value="__EXIT__"))
        
        # Show menu
        console.print("\n[bold green]Use arrow keys to navigate, Space/Enter to toggle[/bold green]")
        console.print("[dim]Scroll through tasks and press Enter to mark as done/undone[/dim]")
        
        selected = questionary.select(
            "Select a task to toggle:",
            choices=choices,
            use_arrow_keys=True
        ).ask()
        
        if selected == "__EXIT__" or selected is None:
            break
        
        # Toggle completion status
        if selected in completion:
            completion[selected] = not completion[selected]
            status = "done" if completion[selected] else "undone"
            console.print(f"[yellow]'{selected}' marked as {status}[/yellow]")
        else:
            completion[selected] = True
            console.print(f"[green]'{selected}' marked as done[/green]")
    
    plan_data['completion_status'] = completion
    plan_data['last_checked'] = datetime.now().isoformat()
    
    return plan_data


def update_markdown_with_checks(plan_content: str, completion_status: dict, jobs: list) -> str:
    """Update markdown content to reflect completion status.
    
    Args:
        plan_content: Original markdown plan content
        completion_status: Dictionary of job_name -> bool
        jobs: List of job dictionaries
    
    Returns:
        Updated markdown content with checked boxes
    """
    lines = plan_content.split('\n')
    
    for job in jobs:
        job_name = job['name']
        user_input = job.get('user_input', '')
        is_done = completion_status.get(job_name, False)
        
        if not is_done:
            continue
            
        # Try multiple matching strategies
        job_words = job_name.lower().split()
        user_words = user_input.lower().split()
        all_words = job_words + user_words
        
        # Strategy 1: Find section header containing job keywords, then mark first checkbox
        section_start = -1
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check if this is a header line
            if line.strip().startswith('#') or line.strip().startswith('##'):
                # Check if any significant job words match in header
                for word in job_words:
                    if len(word) > 2 and word in line_lower:
                        section_start = i
                        break
        
        # If we found a matching section, mark the first checkbox after it
        if section_start >= 0:
            for i in range(section_start + 1, len(lines)):
                line = lines[i]
                # Stop if we hit another header
                if line.strip().startswith('#'):
                    break
                # Mark the first checkbox
                if '- [ ]' in line:
                    lines[i] = line.replace('- [ ]', '- [x]', 1)
                    break
            continue
        
        # Strategy 2: Direct keyword match on any checkbox line
        for i, line in enumerate(lines):
            if '- [ ]' in line:
                line_lower = line.lower()
                for word in all_words:
                    if len(word) > 2 and word in line_lower:
                        lines[i] = line.replace('- [ ]', '- [x]', 1)
                        break
                else:
                    continue
                break
    
    return '\n'.join(lines)


def display_completion_summary(plan_data: dict, console: Console):
    """Display summary of completed tasks.
    
    Args:
        plan_data: Plan data dictionary
        console: Rich console
    """
    completion = plan_data.get('completion_status', {})
    total = len(plan_data.get('jobs', []))
    completed = sum(1 for done in completion.values() if done)
    
    # Create summary table
    table = Table(title="Completion Summary", show_header=True, header_style="bold green")
    table.add_column("Task", style="cyan")
    table.add_column("Status", justify="center")
    
    for job in plan_data.get('jobs', []):
        job_name = job['name']
        is_done = completion.get(job_name, False)
        status = "[green]✓[/green]" if is_done else "[dim]○[/dim]"
        table.add_row(job_name, status)
    
    console.print("\n")
    console.print(table)
    console.print(f"\n[bold]Progress:[/bold] {completed}/{total} tasks completed ({completed*100//total if total > 0 else 0}%)")


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
        
        # Update markdown content with checkmarks
        updated_markdown = update_markdown_with_checks(
            plan_data.get('plan_content', ''),
            plan_data.get('completion_status', {}),
            plan_data.get('jobs', [])
        )
        plan_data['plan_content'] = updated_markdown
        
        # Save updated plan (both JSON and markdown)
        storage.save_plan(plan_data, updated_markdown)
        
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
