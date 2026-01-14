#!/usr/bin/env python3
"""Hierarchical planning module - Year/Month/Week planning with AI assistance."""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.config_loader import load_config
from lib.deepseek_client import DeepSeekClient
from lib.storage import Storage
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.tree import Tree
from rich.prompt import Prompt
import questionary
from questionary import Choice


class HierarchyStorage:
    """Extended storage for hierarchical plans (Year/Month/Week)."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def _get_week_number(self, date: Optional[datetime] = None) -> tuple:
        """Get ISO week number and year for a date.
        
        Returns:
            Tuple of (year, week_number)
        """
        if date is None:
            date = datetime.now()
        iso_cal = date.isocalendar()
        return iso_cal[0], iso_cal[1]  # (year, week)
    
    def get_year_plan_path(self, year: int) -> Path:
        """Get path for year plan."""
        year_dir = self.data_dir / str(year)
        year_dir.mkdir(exist_ok=True)
        return year_dir / "year-plan.json"
    
    def get_month_plan_path(self, year: int, month: int) -> Path:
        """Get path for month plan."""
        month_dir = self.data_dir / str(year) / f"{month:02d}"
        month_dir.mkdir(parents=True, exist_ok=True)
        return month_dir / "month-plan.json"
    
    def get_week_plan_path(self, year: int, week: int) -> Path:
        """Get path for week plan."""
        # Find which month this week belongs to (use Monday of that week)
        jan4 = datetime(year, 1, 4)
        week_start = jan4 + timedelta(weeks=week-1, days=-jan4.weekday())
        month = week_start.month
        
        week_dir = self.data_dir / str(year) / f"{month:02d}" / f"W{week:02d}"
        week_dir.mkdir(parents=True, exist_ok=True)
        return week_dir / "week-plan.json"
    
    def save_plan(self, path: Path, plan_data: Dict[str, Any]) -> None:
        """Save a plan to JSON file."""
        import json
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(plan_data, f, indent=2, ensure_ascii=False)
    
    def load_plan(self, path: Path) -> Optional[Dict[str, Any]]:
        """Load a plan from JSON file."""
        import json
        if not path.exists():
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_current_hierarchy_context(self) -> Dict[str, Any]:
        """Get current year/month/week plans for context."""
        now = datetime.now()
        year = now.year
        month = now.month
        _, week = self._get_week_number(now)
        
        context = {
            'year': year,
            'month': month,
            'week': week,
            'year_plan': self.load_plan(self.get_year_plan_path(year)),
            'month_plan': self.load_plan(self.get_month_plan_path(year, month)),
            'week_plan': self.load_plan(self.get_week_plan_path(year, week))
        }
        return context


def create_week_plan(h_storage: HierarchyStorage, console: Console, client: DeepSeekClient = None):
    """Create or update week plan.
    
    Args:
        h_storage: Hierarchy storage instance
        console: Rich console
        client: Optional DeepSeek client for AI assistance
    """
    now = datetime.now()
    year, week = h_storage._get_week_number(now)
    
    # Calculate week date range
    jan4 = datetime(year, 1, 4)
    week_start = jan4 + timedelta(weeks=week-1, days=-jan4.weekday())
    week_end = week_start + timedelta(days=6)
    
    week_range = f"{week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"
    
    console.print(Panel.fit(
        f"[bold cyan]📅 Week {week} Plan[/bold cyan]\n"
        f"[dim]{week_range}[/dim]",
        border_style="cyan"
    ))
    
    # Load existing week plan
    week_path = h_storage.get_week_plan_path(year, week)
    existing_plan = h_storage.load_plan(week_path)
    
    if existing_plan:
        console.print("\n[yellow]Existing week plan found:[/yellow]")
        console.print(Panel(
            Markdown(existing_plan.get('content', 'No content')),
            border_style="yellow"
        ))
        
        modify = questionary.confirm("Would you like to modify it?").ask()
        if not modify:
            return
    
    # Show parent context (month/year goals if they exist)
    context = h_storage.get_current_hierarchy_context()
    
    if context['month_plan']:
        console.print("\n[dim]📆 This month's focus:[/dim]")
        month_goals = context['month_plan'].get('goals', [])
        for goal in month_goals[:3]:
            console.print(f"  [cyan]•[/cyan] {goal}")
    
    if context['year_plan']:
        console.print("\n[dim]🎯 This year's theme:[/dim]")
        year_theme = context['year_plan'].get('theme', 'Not set')
        console.print(f"  [magenta]{year_theme}[/magenta]")
    
    # Get user input for week goals
    console.print("\n[bold]What are your main goals for this week?[/bold]")
    console.print("[dim]Enter each goal, press Enter twice when done.[/dim]\n")
    
    goals = []
    while True:
        goal = Prompt.ask(f"[cyan]Goal {len(goals)+1}[/cyan]", default="")
        if not goal.strip():
            if goals:
                break
            console.print("[yellow]Please enter at least one goal.[/yellow]")
            continue
        goals.append(goal.strip())
        
        if len(goals) >= 7:
            console.print("[dim]Maximum 7 goals per week.[/dim]")
            break
    
    # Build plan data
    week_plan = {
        'year': year,
        'week': week,
        'week_range': week_range,
        'created': datetime.now().isoformat(),
        'goals': goals,
        'content': None
    }
    
    # Generate AI content if client available
    if client:
        console.print("\n[dim]Generating week plan with AI...[/dim]")
        
        prompt = f"""Create a focused week plan (Week {week}, {week_range}).

Goals for this week:
{chr(10).join(f'- {g}' for g in goals)}

{"Month focus: " + str(context['month_plan'].get('goals', [])[:2]) if context['month_plan'] else ""}
{"Year theme: " + context['year_plan'].get('theme', '') if context['year_plan'] else ""}

Generate a brief, actionable week plan in markdown format with:
1. Week theme (one line)
2. Key priorities (top 3)
3. Daily focus suggestions (Mon-Sun, one line each)

Keep it concise and motivating."""

        messages = [
            {"role": "system", "content": "You are a productivity coach helping plan an effective week."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            ai_content = client.get_completion(messages, use_planning_temp=True)
            week_plan['content'] = ai_content
            
            console.print("\n[bold]Generated Week Plan:[/bold]")
            console.print(Panel(Markdown(ai_content), border_style="green"))
            
            satisfied = questionary.confirm("Save this week plan?").ask()
            if not satisfied:
                # Let user refine
                refinement = Prompt.ask("[cyan]How would you like to adjust it?[/cyan]", default="")
                if refinement:
                    messages.append({"role": "assistant", "content": ai_content})
                    messages.append({"role": "user", "content": f"Please adjust: {refinement}"})
                    ai_content = client.get_completion(messages, use_planning_temp=True)
                    week_plan['content'] = ai_content
                    console.print(Panel(Markdown(ai_content), border_style="green"))
        except Exception as e:
            console.print(f"[red]AI error: {e}[/red]")
            week_plan['content'] = "\n".join(f"- [ ] {g}" for g in goals)
    else:
        # No AI, just use goal list
        week_plan['content'] = "## Week Goals\n\n" + "\n".join(f"- [ ] {g}" for g in goals)
    
    # Save
    h_storage.save_plan(week_path, week_plan)
    console.print(f"\n[green]✓ Week {week} plan saved![/green]")


def create_month_plan(h_storage: HierarchyStorage, console: Console, client: DeepSeekClient = None):
    """Create or update month plan."""
    now = datetime.now()
    year = now.year
    month = now.month
    month_name = now.strftime("%B %Y")
    
    console.print(Panel.fit(
        f"[bold magenta]📆 Month Plan: {month_name}[/bold magenta]",
        border_style="magenta"
    ))
    
    # Load existing
    month_path = h_storage.get_month_plan_path(year, month)
    existing = h_storage.load_plan(month_path)
    
    if existing:
        console.print("\n[yellow]Existing month plan found:[/yellow]")
        for goal in existing.get('goals', []):
            console.print(f"  [cyan]•[/cyan] {goal}")
        
        modify = questionary.confirm("Would you like to modify it?").ask()
        if not modify:
            return
    
    # Get goals
    console.print("\n[bold]What are your main goals for this month?[/bold]")
    console.print("[dim]Enter each goal, press Enter twice when done.[/dim]\n")
    
    goals = []
    while True:
        goal = Prompt.ask(f"[magenta]Goal {len(goals)+1}[/magenta]", default="")
        if not goal.strip():
            if goals:
                break
            console.print("[yellow]Please enter at least one goal.[/yellow]")
            continue
        goals.append(goal.strip())
        
        if len(goals) >= 5:
            console.print("[dim]Maximum 5 goals per month.[/dim]")
            break
    
    month_plan = {
        'year': year,
        'month': month,
        'month_name': month_name,
        'created': datetime.now().isoformat(),
        'goals': goals
    }
    
    h_storage.save_plan(month_path, month_plan)
    console.print(f"\n[green]✓ {month_name} plan saved![/green]")


def create_year_plan(h_storage: HierarchyStorage, console: Console, client: DeepSeekClient = None):
    """Create or update year plan."""
    year = datetime.now().year
    
    console.print(Panel.fit(
        f"[bold yellow]🎯 Year Plan: {year}[/bold yellow]",
        border_style="yellow"
    ))
    
    # Load existing
    year_path = h_storage.get_year_plan_path(year)
    existing = h_storage.load_plan(year_path)
    
    if existing:
        console.print("\n[yellow]Existing year plan:[/yellow]")
        console.print(f"  Theme: [bold]{existing.get('theme', 'Not set')}[/bold]")
        for goal in existing.get('goals', []):
            console.print(f"  [yellow]•[/yellow] {goal}")
        
        modify = questionary.confirm("Would you like to modify it?").ask()
        if not modify:
            return
    
    # Get theme
    theme = Prompt.ask("\n[yellow]What's your theme/word for this year?[/yellow]")
    
    # Get goals
    console.print("\n[bold]What are your major goals for this year?[/bold]")
    console.print("[dim]Enter each goal, press Enter twice when done.[/dim]\n")
    
    goals = []
    while True:
        goal = Prompt.ask(f"[yellow]Goal {len(goals)+1}[/yellow]", default="")
        if not goal.strip():
            if goals:
                break
            console.print("[yellow]Please enter at least one goal.[/yellow]")
            continue
        goals.append(goal.strip())
        
        if len(goals) >= 5:
            console.print("[dim]Maximum 5 goals per year.[/dim]")
            break
    
    year_plan = {
        'year': year,
        'theme': theme,
        'created': datetime.now().isoformat(),
        'goals': goals
    }
    
    h_storage.save_plan(year_path, year_plan)
    console.print(f"\n[green]✓ {year} plan saved![/green]")


def view_hierarchy(h_storage: HierarchyStorage, console: Console):
    """Display plan hierarchy as a tree."""
    context = h_storage.get_current_hierarchy_context()
    
    now = datetime.now()
    
    # Build tree
    tree = Tree(f"[bold]🗂️ Plan Hierarchy ({now.year})[/bold]")
    
    # Year level
    if context['year_plan']:
        yp = context['year_plan']
        year_branch = tree.add(f"[yellow]🎯 Year: {yp.get('theme', 'No theme')}[/yellow]")
        for goal in yp.get('goals', [])[:3]:
            year_branch.add(f"[dim]• {goal}[/dim]")
    else:
        tree.add("[dim]🎯 Year: Not set[/dim]")
    
    # Month level
    if context['month_plan']:
        mp = context['month_plan']
        month_branch = tree.add(f"[magenta]📆 {mp.get('month_name', 'This Month')}[/magenta]")
        for goal in mp.get('goals', [])[:3]:
            month_branch.add(f"[dim]• {goal}[/dim]")
    else:
        tree.add("[dim]📆 Month: Not set[/dim]")
    
    # Week level
    if context['week_plan']:
        wp = context['week_plan']
        week_branch = tree.add(f"[cyan]📅 Week {wp.get('week', '?')}: {wp.get('week_range', '')}[/cyan]")
        for goal in wp.get('goals', [])[:3]:
            week_branch.add(f"[dim]• {goal}[/dim]")
    else:
        tree.add("[dim]📅 Week: Not set[/dim]")
    
    # Daily link
    storage = Storage()
    today_plan = storage.load_plan()
    if today_plan:
        stats = storage.get_today_stats()
        tree.add(f"[green]📋 Today: {stats['completed']}/{stats['total']} done[/green]")
    else:
        tree.add("[dim]📋 Today: No plan[/dim]")
    
    console.print("\n")
    console.print(tree)
    console.print()


def interactive_menu(console: Console):
    """Interactive menu for hierarchy planning."""
    h_storage = HierarchyStorage()
    
    # Try to initialize AI client
    client = None
    try:
        config = load_config()
        deepseek_config = config.get_deepseek_config()
        api_key = config.get_api_key()
        
        client = DeepSeekClient(
            api_key=api_key,
            model=deepseek_config.get('model', 'deepseek-chat'),
            temperature_planning=deepseek_config.get('temperature_planning', 0.0),
            temperature_chat=deepseek_config.get('temperature_chat', 0.7),
            max_tokens=deepseek_config.get('max_tokens', 2000),
            api_base=deepseek_config.get('api_base', 'https://api.deepseek.com')
        )
    except Exception as e:
        console.print(f"[yellow]AI not available: {e}[/yellow]")
    
    while True:
        console.print(Panel.fit(
            "[bold cyan]🗂️ Hierarchical Planning[/bold cyan]\n"
            "[dim]Year → Month → Week → Day[/dim]",
            border_style="cyan"
        ))
        
        # Show current hierarchy
        view_hierarchy(h_storage, console)
        
        choices = [
            Choice("📅 Plan this week", value="week"),
            Choice("📆 Plan this month", value="month"),
            Choice("🎯 Plan this year", value="year"),
            Choice("─" * 30, disabled=True),
            Choice("← Back to main menu", value="exit")
        ]
        
        choice = questionary.select(
            "What would you like to plan?",
            choices=choices,
            use_arrow_keys=True
        ).ask()
        
        if choice == "week":
            create_week_plan(h_storage, console, client)
        elif choice == "month":
            create_month_plan(h_storage, console, client)
        elif choice == "year":
            create_year_plan(h_storage, console, client)
        elif choice == "exit" or choice is None:
            break


def main():
    """Main entry point for hierarchy planning."""
    console = Console()
    
    try:
        interactive_menu(console)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
