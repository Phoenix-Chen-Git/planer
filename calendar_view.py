#!/usr/bin/env python3
"""GitHub-style contribution calendar for the Daily Planner & Logger."""
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.storage import Storage
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table


# Goals storage path
home = Path.home()
GOALS_FILE = home / ".daily_planner" / "data" / "goals.json"


def load_goals() -> Dict:
    """Load goals from storage.
    
    Returns:
        Dictionary with goals data
    """
    if GOALS_FILE.exists():
        with open(GOALS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"goals": [], "archived": []}


def save_goals(goals_data: Dict):
    """Save goals to storage.
    
    Args:
        goals_data: Goals dictionary to save
    """
    GOALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(GOALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(goals_data, f, indent=2, ensure_ascii=False)


def get_stage_info(progress: int) -> Tuple[str, str, str]:
    """Get stage name, emoji, and color based on progress.
    
    Args:
        progress: Progress percentage (0-100)
    
    Returns:
        Tuple of (stage_name, emoji, color)
    """
    if progress <= 10:
        return "Positive", "🌱", "green"  # Starting with good intentions
    elif progress <= 30:
        return "Negative", "🔥", "red"    # Struggle phase
    elif progress <= 50:
        return "Current", "⚡", "yellow"  # Working through it
    else:
        return "Improve", "🚀", "cyan"    # Getting better


def add_goal(console: Console) -> bool:
    """Add a new goal interactively with 4 stages.
    
    Args:
        console: Rich console
    
    Returns:
        True if goal was added
    """
    import questionary
    from questionary import Choice
    
    console.print("\n[bold cyan]🎯 Add New Goal[/bold cyan]\n")
    console.print("[dim]Each goal has 4 stages based on progress:[/dim]")
    console.print("  [green]🌱 Positive (0-10%)[/green] - Starting with good intentions")
    console.print("  [red]🔥 Negative (10-30%)[/red] - Struggle phase")
    console.print("  [yellow]⚡ Current (30-50%)[/yellow] - Working through it")
    console.print("  [cyan]🚀 Improve (50-100%)[/cyan] - Getting better\n")
    
    # Goal name
    name = questionary.text(
        "Goal name:",
        validate=lambda x: len(x.strip()) > 0 or "Goal name cannot be empty"
    ).ask()
    
    if not name:
        return False
    
    # Goal type
    goal_type = questionary.select(
        "Goal type:",
        choices=[
            Choice("🎯 Long-term (1+ year)", value="long_term"),
            Choice("📅 Yearly", value="yearly"),
            Choice("📆 Monthly", value="monthly"),
            Choice("📋 Weekly", value="weekly"),
        ]
    ).ask()
    
    if not goal_type:
        return False
    
    # Priority
    priority = questionary.select(
        "Priority:",
        choices=[
            Choice("🔴 High", value="high"),
            Choice("🟡 Medium", value="medium"),
            Choice("🟢 Low", value="low"),
        ]
    ).ask()
    
    if not priority:
        return False
    
    console.print("\n[bold]Define what each stage means for this goal:[/bold]\n")
    
    # Stage descriptions
    positive_desc = questionary.text(
        "🌱 Positive stage (0-10%) - What does starting well look like?",
        default="Starting with good intentions and motivation"
    ).ask()
    if not positive_desc:
        return False
    
    negative_desc = questionary.text(
        "🔥 Negative stage (10-30%) - What struggles might you face?",
        default="Facing challenges and initial obstacles"
    ).ask()
    if not negative_desc:
        return False
    
    current_desc = questionary.text(
        "⚡ Current stage (30-50%) - What does working through it look like?",
        default="Making steady progress, adapting to challenges"
    ).ask()
    if not current_desc:
        return False
    
    improve_desc = questionary.text(
        "🚀 Improve stage (50-100%) - What does success look like?",
        default="Building momentum, seeing real results"
    ).ask()
    if not improve_desc:
        return False
    
    # Create goal entry with stages
    goals_data = load_goals()
    new_goal = {
        "id": len(goals_data["goals"]) + len(goals_data.get("archived", [])) + 1,
        "name": name.strip(),
        "type": goal_type,
        "priority": priority,
        "created_at": datetime.now().isoformat(),
        "status": "active",
        "progress": 0,
        "stages": {
            "positive": positive_desc.strip(),
            "negative": negative_desc.strip(),
            "current": current_desc.strip(),
            "improve": improve_desc.strip()
        }
    }
    
    goals_data["goals"].append(new_goal)
    save_goals(goals_data)
    
    console.print(f"\n[bold green]✅ Goal '{name}' added successfully![/bold green]")
    console.print(f"[dim]Starting at 🌱 Positive stage (0%)[/dim]")
    return True


def update_goal_progress(console: Console) -> bool:
    """Update progress on a goal.
    
    Args:
        console: Rich console
    
    Returns:
        True if progress was updated
    """
    import questionary
    from questionary import Choice
    
    goals_data = load_goals()
    active_goals = [g for g in goals_data["goals"] if g.get("status") == "active"]
    
    if not active_goals:
        console.print("\n[yellow]No active goals to update.[/yellow]")
        return False
    
    console.print("\n[bold cyan]📈 Update Goal Progress[/bold cyan]\n")
    
    # Select goal with current stage shown
    choices = []
    for g in active_goals:
        stage_name, stage_emoji, _ = get_stage_info(g['progress'])
        choices.append(Choice(
            f"{get_priority_emoji(g['priority'])} {g['name']} ({stage_emoji} {stage_name} {g['progress']}%)",
            value=g['id']
        ))
    choices.append(Choice("❌ Cancel", value=None))
    
    goal_id = questionary.select(
        "Select goal to update:",
        choices=choices
    ).ask()
    
    if goal_id is None:
        return False
    
    # Find the goal and show stages
    selected_goal = None
    for goal in goals_data["goals"]:
        if goal["id"] == goal_id:
            selected_goal = goal
            break
    
    if selected_goal and "stages" in selected_goal:
        console.print(f"\n[bold]{selected_goal['name']}[/bold]")
        console.print("[dim]Stage descriptions:[/dim]")
        console.print(f"  [green]🌱 Positive (0-10%):[/green] {selected_goal['stages'].get('positive', 'N/A')}")
        console.print(f"  [red]🔥 Negative (10-30%):[/red] {selected_goal['stages'].get('negative', 'N/A')}")
        console.print(f"  [yellow]⚡ Current (30-50%):[/yellow] {selected_goal['stages'].get('current', 'N/A')}")
        console.print(f"  [cyan]🚀 Improve (50-100%):[/cyan] {selected_goal['stages'].get('improve', 'N/A')}")
        console.print("")
    
    # Get new progress
    progress_str = questionary.text(
        "New progress (0-100%):",
        validate=lambda x: (x.isdigit() and 0 <= int(x) <= 100) or "Enter a number between 0 and 100"
    ).ask()
    
    if not progress_str:
        return False
    
    progress = int(progress_str)
    old_progress = selected_goal['progress'] if selected_goal else 0
    
    # Update goal
    for goal in goals_data["goals"]:
        if goal["id"] == goal_id:
            goal["progress"] = progress
            goal["last_updated"] = datetime.now().isoformat()
            
            if progress >= 100:
                complete = questionary.confirm(
                    "Goal is 100% complete! Mark as completed?"
                ).ask()
                if complete:
                    goal["status"] = "completed"
                    goal["completed_at"] = datetime.now().isoformat()
            break
    
    save_goals(goals_data)
    
    # Show stage transition
    old_stage, old_emoji, _ = get_stage_info(old_progress)
    new_stage, new_emoji, new_color = get_stage_info(progress)
    
    console.print(f"\n[bold green]✅ Progress updated to {progress}%![/bold green]")
    if old_stage != new_stage:
        console.print(f"[{new_color}]Stage changed: {old_emoji} {old_stage} → {new_emoji} {new_stage}[/{new_color}]")
    else:
        console.print(f"[dim]Current stage: {new_emoji} {new_stage}[/dim]")
    
    return True


def get_priority_emoji(priority: str) -> str:
    """Get emoji for priority level."""
    return {
        "high": "🔴",
        "medium": "🟡",
        "low": "🟢"
    }.get(priority, "⚪")


def get_type_emoji(goal_type: str) -> str:
    """Get emoji for goal type."""
    return {
        "long_term": "🎯",
        "yearly": "📅",
        "monthly": "📆",
        "weekly": "📋"
    }.get(goal_type, "📌")


def display_goals(console: Console):
    """Display goals panel with stages.
    
    Args:
        console: Rich console
    """
    goals_data = load_goals()
    active_goals = [g for g in goals_data["goals"] if g.get("status") == "active"]
    completed_goals = [g for g in goals_data["goals"] if g.get("status") == "completed"]
    
    if not active_goals and not completed_goals:
        console.print(Panel(
            "[dim]No goals set yet. Add a goal to get started![/dim]",
            title="[bold cyan]🎯 Goals[/bold cyan]",
            border_style="cyan"
        ))
        return
    
    # Create goals table
    table = Table(show_header=True, border_style="cyan", expand=True)
    table.add_column("", width=2)  # Priority
    table.add_column("Goal", style="white")
    table.add_column("Stage", justify="center", width=12)
    table.add_column("Progress", justify="left", width=18)
    
    # Sort by priority
    priority_order = {"high": 0, "medium": 1, "low": 2}
    active_goals.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 3))
    
    for goal in active_goals:
        progress = goal.get("progress", 0)
        stage_name, stage_emoji, stage_color = get_stage_info(progress)
        
        # Progress bar with stage color
        bar_width = 10
        filled = int(bar_width * progress / 100)
        empty = bar_width - filled
        
        progress_bar = f"[{stage_color}]{'█' * filled}[/{stage_color}][dim]{'░' * empty}[/dim] {progress}%"
        stage_display = f"[{stage_color}]{stage_emoji} {stage_name}[/{stage_color}]"
        
        table.add_row(
            get_priority_emoji(goal.get("priority", "low")),
            goal["name"],
            stage_display,
            progress_bar
        )
    
    # Show completed goals count
    if completed_goals:
        table.add_row("", "", "", "")
        table.add_row(
            "✅",
            f"[dim]{len(completed_goals)} goal(s) completed[/dim]",
            "",
            ""
        )
    
    console.print("\n")
    console.print(Panel(
        table,
        title="[bold cyan]🎯 Goals[/bold cyan]",
        border_style="cyan",
        padding=(0, 1)
    ))


def manage_goals(console: Console):
    """Manage goals menu.
    
    Args:
        console: Rich console
    """
    import questionary
    from questionary import Choice
    
    while True:
        console.clear()
        display_goals(console)
        
        # Check if review is due
        review_reminder = check_review_due()
        if review_reminder:
            console.print(f"\n[yellow]⏰ {review_reminder}[/yellow]")
        
        choices = [
            Choice("➕ Add new goal", value="add"),
            Choice("📈 Update progress", value="progress"),
            Choice("🔍 Review goals", value="review"),
            Choice("📋 View all goals", value="view"),
            Choice("📊 View past reviews", value="past_reviews"),
            Choice("🗑️ Archive/Delete goal", value="archive"),
            Choice("❌ Back", value="back")
        ]
        
        result = questionary.select(
            "\nGoal management:",
            choices=choices,
            use_arrow_keys=True
        ).ask()
        
        if result == "add":
            add_goal(console)
            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()
        elif result == "progress":
            update_goal_progress(console)
            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()
        elif result == "review":
            do_goal_review(console)
            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()
        elif result == "view":
            view_all_goals(console)
            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()
        elif result == "past_reviews":
            view_past_reviews(console)
            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()
        elif result == "archive":
            archive_goal(console)
            console.print("\n[dim]Press Enter to continue...[/dim]")
            input()
        elif result == "back" or result is None:
            break


def check_review_due() -> Optional[str]:
    """Check if any review is due.
    
    Returns:
        Reminder message if review is due, None otherwise
    """
    goals_data = load_goals()
    reviews = goals_data.get("reviews", [])
    now = datetime.now()
    
    # Get last review dates by type
    last_weekly = None
    last_monthly = None
    last_yearly = None
    
    for review in reviews:
        review_date = datetime.fromisoformat(review["date"])
        review_type = review["type"]
        
        if review_type == "weekly":
            if not last_weekly or review_date > last_weekly:
                last_weekly = review_date
        elif review_type == "monthly":
            if not last_monthly or review_date > last_monthly:
                last_monthly = review_date
        elif review_type == "yearly":
            if not last_yearly or review_date > last_yearly:
                last_yearly = review_date
    
    reminders = []
    
    # Check weekly (7 days)
    if not last_weekly or (now - last_weekly).days >= 7:
        reminders.append("Weekly review due!")
    
    # Check monthly (30 days)
    if not last_monthly or (now - last_monthly).days >= 30:
        reminders.append("Monthly review due!")
    
    # Check yearly (365 days)
    if not last_yearly or (now - last_yearly).days >= 365:
        reminders.append("Yearly review due!")
    
    return " | ".join(reminders) if reminders else None


def do_goal_review(console: Console) -> bool:
    """Perform a goal review session.
    
    Args:
        console: Rich console
    
    Returns:
        True if review was completed
    """
    import questionary
    from questionary import Choice
    
    goals_data = load_goals()
    active_goals = [g for g in goals_data["goals"] if g.get("status") == "active"]
    
    if not active_goals:
        console.print("\n[yellow]No active goals to review.[/yellow]")
        return False
    
    console.print("\n[bold cyan]🔍 Goal Review Session[/bold cyan]\n")
    
    # Select review type
    review_type = questionary.select(
        "What type of review?",
        choices=[
            Choice("📅 Weekly Review", value="weekly"),
            Choice("📆 Monthly Review", value="monthly"),
            Choice("🗓️ Yearly Review", value="yearly"),
            Choice("❌ Cancel", value=None)
        ]
    ).ask()
    
    if not review_type:
        return False
    
    type_descriptions = {
        "weekly": "Reflect on the past week",
        "monthly": "Reflect on the past month",
        "yearly": "Reflect on the past year"
    }
    
    console.print(f"\n[bold]{type_descriptions[review_type]}[/bold]\n")
    console.print("[dim]For each goal, you'll reflect on your progress.[/dim]\n")
    
    review_entries = []
    
    for goal in active_goals:
        progress = goal.get("progress", 0)
        stage_name, stage_emoji, stage_color = get_stage_info(progress)
        
        console.print(f"\n[bold cyan]━━━ {goal['name']} ━━━[/bold cyan]")
        console.print(f"[{stage_color}]{stage_emoji} {stage_name} ({progress}%)[/{stage_color}]")
        
        # Show stage descriptions if available
        if "stages" in goal:
            console.print(f"[dim]Current stage: {goal['stages'].get(stage_name.lower(), 'N/A')}[/dim]")
        
        console.print("")
        
        # What have you done?
        done = questionary.text(
            "✅ What have you DONE towards this goal?",
            multiline=False
        ).ask()
        if done is None:
            return False
        
        # What haven't you done?
        not_done = questionary.text(
            "❌ What have you NOT done that you should have?",
            multiline=False
        ).ask()
        if not_done is None:
            return False
        
        # Are you getting closer?
        closer = questionary.select(
            "📍 Are you getting closer to this goal?",
            choices=[
                Choice("🚀 Yes, making great progress!", value="great"),
                Choice("👍 Yes, steady progress", value="steady"),
                Choice("➡️ Staying about the same", value="same"),
                Choice("👎 No, falling behind", value="behind"),
                Choice("🆘 No, need to rethink this goal", value="rethink")
            ]
        ).ask()
        if not closer:
            return False
        
        # Next actions
        next_actions = questionary.text(
            "🎯 What will you do next to progress?",
            multiline=False
        ).ask()
        if next_actions is None:
            return False
        
        # Optional: Update progress
        update = questionary.confirm(
            f"📈 Update progress? (Currently {progress}%)"
        ).ask()
        
        new_progress = progress
        if update:
            progress_str = questionary.text(
                "New progress (0-100%):",
                default=str(progress),
                validate=lambda x: (x.isdigit() and 0 <= int(x) <= 100) or "Enter 0-100"
            ).ask()
            if progress_str:
                new_progress = int(progress_str)
                # Update goal progress
                for g in goals_data["goals"]:
                    if g["id"] == goal["id"]:
                        g["progress"] = new_progress
                        g["last_updated"] = datetime.now().isoformat()
                        break
        
        review_entries.append({
            "goal_id": goal["id"],
            "goal_name": goal["name"],
            "progress_before": progress,
            "progress_after": new_progress,
            "done": done.strip() if done else "",
            "not_done": not_done.strip() if not_done else "",
            "closer": closer,
            "next_actions": next_actions.strip() if next_actions else ""
        })
    
    # Overall reflection
    console.print("\n[bold cyan]━━━ Overall Reflection ━━━[/bold cyan]\n")
    
    overall = questionary.text(
        "💭 Any overall thoughts or insights?",
        multiline=False
    ).ask()
    
    # Save review
    if "reviews" not in goals_data:
        goals_data["reviews"] = []
    
    review = {
        "date": datetime.now().isoformat(),
        "type": review_type,
        "entries": review_entries,
        "overall": overall.strip() if overall else ""
    }
    
    goals_data["reviews"].append(review)
    save_goals(goals_data)
    
    # Summary
    console.print("\n[bold green]✅ Review saved![/bold green]\n")
    console.print(f"[dim]Type: {review_type.capitalize()} Review[/dim]")
    console.print(f"[dim]Goals reviewed: {len(review_entries)}[/dim]")
    
    # Show any significant changes
    for entry in review_entries:
        if entry["progress_before"] != entry["progress_after"]:
            diff = entry["progress_after"] - entry["progress_before"]
            sign = "+" if diff > 0 else ""
            console.print(f"  📈 {entry['goal_name']}: {entry['progress_before']}% → {entry['progress_after']}% ({sign}{diff}%)")
    
    return True


def view_past_reviews(console: Console):
    """View past goal reviews.
    
    Args:
        console: Rich console
    """
    import questionary
    from questionary import Choice
    
    goals_data = load_goals()
    reviews = goals_data.get("reviews", [])
    
    if not reviews:
        console.print("\n[yellow]No reviews yet. Complete a review first![/yellow]")
        return
    
    console.print("\n[bold cyan]📊 Past Reviews[/bold cyan]\n")
    
    # Group by type
    type_emoji = {"weekly": "📅", "monthly": "📆", "yearly": "🗓️"}
    
    # Show recent reviews (last 10)
    recent = sorted(reviews, key=lambda x: x["date"], reverse=True)[:10]
    
    choices = []
    for i, review in enumerate(recent):
        review_date = datetime.fromisoformat(review["date"])
        date_str = review_date.strftime("%Y-%m-%d %H:%M")
        emoji = type_emoji.get(review["type"], "📋")
        choices.append(Choice(
            f"{emoji} {review['type'].capitalize()} - {date_str}",
            value=i
        ))
    
    choices.append(Choice("❌ Back", value=None))
    
    selected = questionary.select(
        "Select a review to view:",
        choices=choices
    ).ask()
    
    if selected is None:
        return
    
    # Show selected review
    review = recent[selected]
    review_date = datetime.fromisoformat(review["date"])
    
    console.print(f"\n[bold cyan]━━━ {review['type'].capitalize()} Review ━━━[/bold cyan]")
    console.print(f"[dim]{review_date.strftime('%A, %B %d, %Y at %I:%M %p')}[/dim]\n")
    
    for entry in review["entries"]:
        console.print(f"[bold]{entry['goal_name']}[/bold]")
        console.print(f"  Progress: {entry['progress_before']}% → {entry['progress_after']}%")
        
        if entry.get("done"):
            console.print(f"  [green]✅ Done:[/green] {entry['done']}")
        if entry.get("not_done"):
            console.print(f"  [red]❌ Not done:[/red] {entry['not_done']}")
        
        closer_text = {
            "great": "🚀 Making great progress!",
            "steady": "👍 Steady progress",
            "same": "➡️ Staying about the same",
            "behind": "👎 Falling behind",
            "rethink": "🆘 Need to rethink"
        }
        console.print(f"  [dim]{closer_text.get(entry.get('closer', ''), '')}[/dim]")
        
        if entry.get("next_actions"):
            console.print(f"  [cyan]🎯 Next:[/cyan] {entry['next_actions']}")
        console.print("")
    
    if review.get("overall"):
        console.print(f"[bold]💭 Overall:[/bold] {review['overall']}")


def view_all_goals(console: Console):
    """View detailed goals list.
    
    Args:
        console: Rich console
    """
    goals_data = load_goals()
    all_goals = goals_data["goals"]
    
    if not all_goals:
        console.print("\n[yellow]No goals found.[/yellow]")
        return
    
    console.print("\n[bold cyan]📋 All Goals[/bold cyan]\n")
    
    # Group by type
    by_type = {}
    for goal in all_goals:
        goal_type = goal.get("type", "other")
        if goal_type not in by_type:
            by_type[goal_type] = []
        by_type[goal_type].append(goal)
    
    type_names = {
        "long_term": "🎯 Long-term Goals",
        "yearly": "📅 Yearly Goals",
        "monthly": "📆 Monthly Goals",
        "weekly": "📋 Weekly Goals"
    }
    
    for goal_type, goals in by_type.items():
        console.print(f"\n[bold]{type_names.get(goal_type, goal_type)}[/bold]")
        console.print("[dim]" + "─" * 40 + "[/dim]")
        
        for goal in goals:
            status_icon = "✅" if goal.get("status") == "completed" else "⏳"
            progress = goal.get("progress", 0)
            priority = get_priority_emoji(goal.get("priority", "low"))
            
            console.print(f"  {status_icon} {priority} {goal['name']} - {progress}%")
            if goal.get("description"):
                console.print(f"      [dim]{goal['description']}[/dim]")


def archive_goal(console: Console) -> bool:
    """Archive or delete a goal.
    
    Args:
        console: Rich console
    
    Returns:
        True if goal was archived
    """
    import questionary
    from questionary import Choice
    
    goals_data = load_goals()
    
    if not goals_data["goals"]:
        console.print("\n[yellow]No goals to archive.[/yellow]")
        return False
    
    console.print("\n[bold cyan]🗑️ Archive Goal[/bold cyan]\n")
    
    choices = [
        Choice(f"{get_priority_emoji(g['priority'])} {g['name']}", value=g['id'])
        for g in goals_data["goals"]
    ]
    choices.append(Choice("❌ Cancel", value=None))
    
    goal_id = questionary.select(
        "Select goal to archive:",
        choices=choices
    ).ask()
    
    if goal_id is None:
        return False
    
    # Find and archive
    for i, goal in enumerate(goals_data["goals"]):
        if goal["id"] == goal_id:
            goal["archived_at"] = datetime.now().isoformat()
            if "archived" not in goals_data:
                goals_data["archived"] = []
            goals_data["archived"].append(goal)
            goals_data["goals"].pop(i)
            break
    
    save_goals(goals_data)
    console.print("\n[bold green]✅ Goal archived![/bold green]")
    return True


def get_contribution_data(storage: Storage, weeks: int = 52) -> Dict[str, Dict]:
    """Get contribution data for the specified number of weeks.
    
    Args:
        storage: Storage instance
        weeks: Number of weeks to look back (default: 52 for a full year)
    
    Returns:
        Dictionary mapping date strings to activity data
    """
    contributions = {}
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks)
    
    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        plan = storage.load_plan(current)
        
        if plan:
            completion = plan.get('completion_status', {})
            jobs = plan.get('jobs', [])
            
            # Count tasks recursively
            def count_tasks(job_list):
                completed = quit_count = pending = 0
                for job in job_list:
                    job_name = job.get('name') or job.get('task_name', 'Unknown')
                    status = completion.get(job_name)
                    
                    if status == 'done' or status is True:
                        completed += 1
                    elif status == 'quit':
                        quit_count += 1
                    else:
                        pending += 1
                    
                    sub_jobs = job.get('sub_jobs', [])
                    if sub_jobs:
                        sub_stats = count_tasks(sub_jobs)
                        completed += sub_stats[0]
                        quit_count += sub_stats[1]
                        pending += sub_stats[2]
                
                return completed, quit_count, pending
            
            completed, quit_count, pending = count_tasks(jobs)
            total = completed + quit_count + pending
            
            contributions[date_str] = {
                'completed': completed,
                'quit': quit_count,
                'pending': pending,
                'total': total,
                'has_plan': True
            }
        else:
            contributions[date_str] = {
                'completed': 0,
                'quit': 0,
                'pending': 0,
                'total': 0,
                'has_plan': False
            }
        
        current += timedelta(days=1)
    
    return contributions


def get_intensity_level(completed: int, total: int) -> int:
    """Get intensity level (0-4) based on completion.
    
    Args:
        completed: Number of completed tasks
        total: Total number of tasks
    
    Returns:
        Intensity level from 0 (none) to 4 (high)
    """
    if total == 0:
        return 0
    
    percentage = (completed / total) * 100
    
    if percentage == 0:
        return 0
    elif percentage < 25:
        return 1
    elif percentage < 50:
        return 2
    elif percentage < 75:
        return 3
    else:
        return 4


def get_block_style(intensity: int, has_plan: bool) -> Tuple[str, str]:
    """Get the block character and style based on intensity.
    
    Args:
        intensity: Level from 0-4
        has_plan: Whether there was a plan for this day
    
    Returns:
        Tuple of (character, rich style)
    """
    if not has_plan:
        return "□", "dim"
    
    # GitHub-like green color gradient
    styles = [
        ("□", "dim"),           # 0: No activity
        ("▪", "green4"),        # 1: Low (dark green)
        ("▪", "green3"),        # 2: Medium-low
        ("▪", "green1"),        # 3: Medium-high
        ("▪", "bold bright_green"),  # 4: High (bright green)
    ]
    
    return styles[intensity]


def display_calendar(storage: Storage, console: Console, weeks: int = 52, show_goals: bool = True):
    """Display the GitHub-style contribution calendar.
    
    Args:
        storage: Storage instance
        console: Rich console
        weeks: Number of weeks to display (default: 52 for full year)
        show_goals: Whether to show goals panel
    """
    contributions = get_contribution_data(storage, weeks)
    
    # Get date range
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks)
    
    # Align to Sunday (start of week)
    start_date -= timedelta(days=start_date.weekday() + 1)
    if start_date.weekday() != 6:  # Adjust to Sunday
        start_date -= timedelta(days=(start_date.weekday() + 1) % 7)
    
    # Build the calendar grid
    # Days of week labels (vertical on left)
    day_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    
    # Calculate total completed tasks and active days
    total_completed = sum(d['completed'] for d in contributions.values())
    active_days = sum(1 for d in contributions.values() if d['completed'] > 0)
    
    # Build calendar rows
    calendar_lines = []
    
    # Month labels header
    month_header = Text("     ")  # Spacing for day labels
    current_date = start_date
    prev_month = -1
    month_positions = []
    
    for week in range(weeks):
        week_start = start_date + timedelta(weeks=week)
        if week_start.month != prev_month:
            month_name = week_start.strftime("%b")
            month_positions.append((week, month_name))
            prev_month = week_start.month
    
    # Create month header line
    month_line = ["     "]  # Spacing
    last_pos = 0
    for pos, month_name in month_positions:
        # Add spacing
        spaces_needed = pos - last_pos
        month_line.append(" " * (spaces_needed * 2))
        month_line.append(month_name)
        last_pos = pos + len(month_name) // 2
    
    calendar_lines.append(Text("".join(month_line), style="dim"))
    
    # Build each day row (7 rows for each day of week)
    for day_idx in range(7):
        row = Text()
        
        # Day label (only show Mon, Wed, Fri for cleaner look)
        if day_idx in [1, 3, 5]:
            row.append(f"{day_labels[day_idx]:>4} ", style="dim")
        else:
            row.append("     ")
        
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
                    row.append(" ")  # Future dates are empty
                else:
                    row.append(char, style=style)
            else:
                row.append(" ")
            
            row.append(" ")  # Spacing between weeks
        
        calendar_lines.append(row)
    
    # Add legend
    legend = Text("\n     Less ")
    legend.append("□", style="dim")
    legend.append(" ")
    legend.append("▪", style="green4")
    legend.append(" ")
    legend.append("▪", style="green3")
    legend.append(" ")
    legend.append("▪", style="green1")
    legend.append(" ")
    legend.append("▪", style="bold bright_green")
    legend.append(" More", style="dim")
    legend.append("    ", style="dim")
    legend.append("◉", style="bold cyan")
    legend.append(" Today", style="dim")
    
    calendar_lines.append(legend)
    
    # Stats line
    stats = Text(f"\n     📊 {total_completed} tasks completed across {active_days} active days")
    stats.stylize("dim")
    calendar_lines.append(stats)
    
    # Calculate streak
    streak = storage.calculate_streak()
    if streak > 0:
        streak_line = Text(f"     🔥 Current streak: {streak} days")
        if streak >= 7:
            streak_line.stylize("bold green")
        elif streak >= 3:
            streak_line.stylize("yellow")
        else:
            streak_line.stylize("dim")
        calendar_lines.append(streak_line)
    
    # Create the panel
    content = Text("\n").join(calendar_lines)
    
    console.print("\n")
    console.print(Panel(
        content,
        title="[bold cyan]📅 Contribution Calendar[/bold cyan]",
        subtitle=f"[dim]{start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}[/dim]",
        border_style="cyan",
        padding=(1, 2)
    ))
    
    # Show goals if enabled
    if show_goals:
        display_goals(console)


def display_detailed_view(storage: Storage, console: Console, month: Optional[int] = None, year: Optional[int] = None):
    """Display a detailed monthly view with task breakdowns.
    
    Args:
        storage: Storage instance
        console: Rich console
        month: Month to display (default: current month)
        year: Year to display (default: current year)
    """
    now = datetime.now()
    if month is None:
        month = now.month
    if year is None:
        year = now.year
    
    # Get first and last day of month
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)
    
    # Create table
    table = Table(title=f"📊 {first_day.strftime('%B %Y')} Details", border_style="cyan")
    table.add_column("Date", style="cyan", justify="center")
    table.add_column("Day", style="dim", justify="center")
    table.add_column("✅ Done", justify="center")
    table.add_column("🚫 Quit", justify="center")
    table.add_column("⏳ Pending", justify="center")
    table.add_column("Progress", justify="left")
    
    current = first_day
    while current <= last_day and current <= now:
        plan = storage.load_plan(current)
        
        if plan:
            completion = plan.get('completion_status', {})
            jobs = plan.get('jobs', [])
            
            def count_tasks(job_list):
                completed = quit_count = pending = 0
                for job in job_list:
                    job_name = job.get('name') or job.get('task_name', 'Unknown')
                    status = completion.get(job_name)
                    
                    if status == 'done' or status is True:
                        completed += 1
                    elif status == 'quit':
                        quit_count += 1
                    else:
                        pending += 1
                    
                    sub_jobs = job.get('sub_jobs', [])
                    if sub_jobs:
                        sub_stats = count_tasks(sub_jobs)
                        completed += sub_stats[0]
                        quit_count += sub_stats[1]
                        pending += sub_stats[2]
                
                return completed, quit_count, pending
            
            completed, quit_count, pending = count_tasks(jobs)
            total = completed + quit_count + pending
            
            # Create progress bar
            bar_width = 15
            if total > 0:
                filled = int(bar_width * completed / total)
                empty = bar_width - filled
                
                intensity = get_intensity_level(completed, total)
                if intensity >= 3:
                    bar_color = "green"
                elif intensity >= 2:
                    bar_color = "yellow"
                else:
                    bar_color = "red"
                
                progress = f"[{bar_color}]{'█' * filled}[/{bar_color}][dim]{'░' * empty}[/dim] {completed}/{total}"
            else:
                progress = "[dim]No tasks[/dim]"
            
            # Highlight today
            date_style = "bold cyan" if current.date() == now.date() else ""
            
            table.add_row(
                f"[{date_style}]{current.day}[/{date_style}]" if date_style else str(current.day),
                current.strftime("%a"),
                f"[green]{completed}[/green]" if completed > 0 else "[dim]0[/dim]",
                f"[yellow]{quit_count}[/yellow]" if quit_count > 0 else "[dim]0[/dim]",
                f"[red]{pending}[/red]" if pending > 0 else "[dim]0[/dim]",
                progress
            )
        else:
            date_style = "bold cyan" if current.date() == now.date() else "dim"
            table.add_row(
                f"[{date_style}]{current.day}[/{date_style}]",
                current.strftime("%a"),
                "[dim]-[/dim]",
                "[dim]-[/dim]",
                "[dim]-[/dim]",
                "[dim]No plan[/dim]"
            )
        
        current += timedelta(days=1)
    
    console.print("\n")
    console.print(table)


def main():
    """Main entry point for calendar view."""
    import questionary
    from questionary import Choice
    
    console = Console()
    storage = Storage()
    
    # Show year view by default on startup
    console.clear()
    display_calendar(storage, console, weeks=52, show_goals=True)
    
    while True:
        choices = [
            Choice("📊 Year view (52 weeks)", value="year"),
            Choice("📅 Half year view (26 weeks)", value="half"),
            Choice("🗓️ Quarter view (13 weeks)", value="quarter"),
            Choice("📋 Monthly detail view", value="monthly"),
            Choice("─" * 30, disabled=True),
            Choice("🎯 Manage goals", value="goals"),
            Choice("❌ Exit", value="exit")
        ]
        
        result = questionary.select(
            "\nSelect option:",
            choices=choices,
            use_arrow_keys=True
        ).ask()
        
        if result == "year":
            console.clear()
            display_calendar(storage, console, weeks=52)
        elif result == "half":
            console.clear()
            display_calendar(storage, console, weeks=26)
        elif result == "quarter":
            console.clear()
            display_calendar(storage, console, weeks=13)
        elif result == "monthly":
            console.clear()
            display_detailed_view(storage, console)
            display_goals(console)
        elif result == "goals":
            manage_goals(console)
            console.clear()
            display_calendar(storage, console, weeks=52)
        elif result == "exit" or result is None:
            break
    
    console.print("\n[bold green]Goodbye! 👋[/bold green]\n")


if __name__ == "__main__":
    main()
