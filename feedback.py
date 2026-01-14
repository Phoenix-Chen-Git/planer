#!/usr/bin/env python3
"""Feedback viewer - display and manage tool improvement suggestions."""
import sys
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.config_loader import load_config
from lib.deepseek_client import DeepSeekClient
from lib.storage import Storage
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Prompt
import questionary
from datetime import datetime


def display_feedback(storage: Storage, console: Console, show_archived: bool = False):
    """Display feedback entries in a table.
    
    Args:
        storage: Storage instance
        console: Rich console
        show_archived: If True, show archived entries instead of pending
    """
    if show_archived:
        feedback_data = storage.load_archived_feedback()
        entries = feedback_data.get('archived_entries', [])
        title = "Archived Feedback (Implemented/Dismissed)"
    else:
        feedback_data = storage.load_all_feedback()
        entries = feedback_data.get('feedback_entries', [])
        # Filter to only pending
        entries = [e for e in entries if e.get('status', 'pending') == 'pending']
        title = "Pending Feedback"
    
    if not entries:
        if show_archived:
            console.print("[yellow]No archived feedback entries.[/yellow]")
        else:
            console.print("[green]✓ No pending feedback! All clear.[/green]")
        return entries
    
    # Create summary table
    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=3)
    table.add_column("Date", style="cyan", width=12)
    if show_archived:
        table.add_column("Status", justify="center", width=12)
    table.add_column("Feedback", style="white", width=50)
    
    for i, entry in enumerate(entries):
        date_str = entry.get('date', 'Unknown')
        try:
            date_obj = datetime.fromisoformat(date_str)
            date_display = date_obj.strftime("%Y-%m-%d")
        except:
            date_display = date_str[:10]
        
        original = entry.get('original_feedback', 'N/A')
        # Truncate if too long
        if len(original) > 47:
            original = original[:44] + "..."
        
        if show_archived:
            status = entry.get('status', 'pending')
            status_style = {
                'implemented': '[green]✓ Done[/green]',
                'dismissed': '[dim]Dismissed[/dim]'
            }.get(status, status)
            table.add_row(str(i), date_display, status_style, original)
        else:
            table.add_row(str(i), date_display, original)
    
    console.print("\n")
    console.print(table)
    console.print(f"\n[dim]Total: {len(entries)} entries[/dim]")
    
    return entries


def show_feedback_detail(entry: dict, index: int, console: Console):
    """Show detailed view of a feedback entry.
    
    Args:
        entry: Feedback entry dictionary
        index: Entry index
        console: Rich console
    """
    date_str = entry.get('date', 'Unknown')
    try:
        date_obj = datetime.fromisoformat(date_str)
        date_display = date_obj.strftime("%Y-%m-%d %H:%M")
    except:
        date_display = date_str
    
    console.print(f"\n[bold cyan]Feedback Entry #{index}[/bold cyan]")
    console.print(f"[dim]Date: {date_display}[/dim]")
    console.print(f"[dim]Status: {entry.get('status', 'pending')}[/dim]\n")
    
    # Original feedback
    console.print("[bold]Your Feedback:[/bold]")
    console.print(Panel(entry.get('original_feedback', 'N/A'), border_style="yellow"))
    
    # AI Understanding
    console.print("\n[bold]DeepSeek's Understanding:[/bold]")
    final_understanding = entry.get('final_understanding', 'N/A')
    console.print(Panel(
        Markdown(final_understanding),
        border_style="magenta"
    ))
    
    # Understanding history if exists
    history = entry.get('understanding_history', [])
    if len(history) > 1:
        console.print(f"\n[dim]({len(history)} refinement iterations)[/dim]")
        console.print(f"[bold]Understanding History:[/bold]")
        for i, item in enumerate(history, 1):
            console.print(f"\n[cyan]Round {i}:[/cyan]")
            console.print(f"  [dim]You:[/dim] {item['user_input']}")
            console.print(f"  [dim]AI:[/dim] {item['ai_understanding']}")


def add_new_feedback(storage: Storage, console: Console):
    """Add new feedback entry.
    
    Args:
        storage: Storage instance
        console: Rich console
    """
    # Check pending feedback limit
    pending_count = storage.count_pending_feedback()
    MAX_PENDING = 10
    
    if pending_count >= MAX_PENDING:
        console.print(f"\n[red]✗ Cannot add feedback: You have {pending_count} pending items![/red]")
        console.print(f"[yellow]Please resolve some pending feedback before adding new ones.[/yellow]")
        console.print("[dim]Mark items as 'Implemented' or 'Dismissed' to archive them.[/dim]\n")
        return
    
    remaining = MAX_PENDING - pending_count
    console.print(f"\n[bold cyan]Add Tool Improvement Feedback[/bold cyan]")
    console.print(f"[dim]({remaining} slots remaining out of {MAX_PENDING})[/dim]\n")
    
    # Get initial feedback
    tool_feedback = Prompt.ask("[yellow]What would you like to improve about this tool?[/yellow]")
    
    if not tool_feedback.strip():
        console.print("[yellow]No feedback provided.[/yellow]")
        return
    
    # Initialize DeepSeek client
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
        console.print(f"[red]Failed to initialize AI: {e}[/red]")
        console.print("[yellow]Saving feedback without AI confirmation...[/yellow]")
        
        # Save without AI understanding
        feedback_entry = {
            'date': datetime.now().isoformat(),
            'original_feedback': tool_feedback,
            'final_understanding': tool_feedback,
            'understanding_history': [],
            'status': 'pending'
        }
        storage.save_feedback(feedback_entry)
        console.print("[green]✓ Feedback saved![/green]")
        return
    
    # AI understanding workflow
    understanding_history = []
    user_description = tool_feedback
    
    while True:
        # Get AI's understanding
        system_prompt = "You are helping understand user feedback about a daily planning tool. The user will describe what they want improved. Confirm your understanding of their request in a clear, concise way."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User feedback: {user_description}\n\nPlease confirm your understanding of what the user wants."}
        ]
        
        try:
            ai_understanding = client.get_completion(messages, use_planning_temp=True)
        except Exception as e:
            console.print(f"[red]AI error: {e}[/red]")
            break
        
        # Display AI's understanding
        console.print("\n[bold]DeepSeek's Understanding:[/bold]")
        console.print(Markdown(ai_understanding))
        
        # Record this round
        understanding_history.append({
            'user_input': user_description,
            'ai_understanding': ai_understanding
        })
        
        # Ask if user is satisfied
        console.print()
        satisfied = questionary.select(
            "Is this understanding correct?",
            choices=["Yes", "No", "Refine"],
            use_arrow_keys=True
        ).ask()
        
        if satisfied == "Yes":
            console.print("[green]✓ Great! Your feedback has been recorded.[/green]")
            break
        elif satisfied == "Refine":
            refinement = Prompt.ask("[cyan]How would you like to refine your description?[/cyan]")
            if refinement.strip():
                user_description = refinement
            else:
                console.print("[yellow]No refinement provided. Using current understanding.[/yellow]")
                break
        else:  # "No"
            new_description = Prompt.ask("[cyan]Please describe what you want again[/cyan]")
            if new_description.strip():
                user_description = new_description
            else:
                console.print("[yellow]No new description provided. Using current understanding.[/yellow]")
                break
    
    # Save feedback
    feedback_entry = {
        'date': datetime.now().isoformat(),
        'original_feedback': tool_feedback,
        'final_understanding': ai_understanding if understanding_history else tool_feedback,
        'understanding_history': understanding_history,
        'status': 'pending'
    }
    
    storage.save_feedback(feedback_entry)
    console.print("\n[green]✓ Feedback saved successfully![/green]")


def interactive_menu(storage: Storage, console: Console):
    """Interactive menu to view and manage feedback.
    
    Args:
        storage: Storage instance
        console: Rich console
    """
    show_archived = False
    
    while True:
        # Display current feedback based on mode
        console.print("\n")
        entries = display_feedback(storage, console, show_archived=show_archived)
        
        # Show pending count limit
        if not show_archived:
            pending_count = storage.count_pending_feedback()
            console.print(f"[dim]Pending: {pending_count}/10 slots used[/dim]")
        
        # Build menu choices
        choices = []
        
        if show_archived:
            choices.append("← Back to pending")
        else:
            choices.append("Add new feedback")
            choices.append("📁 View archived")
        
        choices.append("─" * 40)
        
        if entries:
            # Add view options for each entry
            for i, entry in enumerate(entries):
                feedback_preview = entry.get('original_feedback', 'N/A')
                if len(feedback_preview) > 50:
                    feedback_preview = feedback_preview[:47] + "..."
                if show_archived:
                    status = entry.get('status', 'pending')
                    status_emoji = {'implemented': '✓', 'dismissed': '✕'}.get(status, '○')
                    choices.append(f"[{i}] {status_emoji} {feedback_preview}")
                else:
                    choices.append(f"[{i}] ○ {feedback_preview}")
            
            if not show_archived:
                choices.append("─" * 40)
                choices.append("Mark as done (archive)")
        
        choices.append("Exit")
        
        # Show menu
        console.print()
        choice = questionary.select(
            "What would you like to do?",
            choices=choices,
            use_arrow_keys=True
        ).ask()
        
        if not choice or choice == "Exit":
            console.print("\n[green]Goodbye![/green]\n")
            break
        
        elif choice == "← Back to pending":
            show_archived = False
            continue
        
        elif choice == "📁 View archived":
            show_archived = True
            continue
        
        elif choice == "Add new feedback":
            add_new_feedback(storage, console)
            continue
        
        elif choice == "Mark as done (archive)":
            if not entries:
                console.print("[yellow]No pending feedback to mark.[/yellow]")
                continue
            
            # Get all pending entries with their original indices
            feedback_data = storage.load_all_feedback()
            all_entries = feedback_data.get('feedback_entries', [])
            pending_with_indices = [(i, e) for i, e in enumerate(all_entries) 
                                    if e.get('status', 'pending') == 'pending']
            
            # Select which entry to mark
            entry_choices = []
            for orig_idx, entry in pending_with_indices:
                feedback_preview = entry.get('original_feedback', 'N/A')
                if len(feedback_preview) > 50:
                    feedback_preview = feedback_preview[:47] + "..."
                entry_choices.append(f"[{orig_idx}] {feedback_preview}")
            
            entry_choice = questionary.select(
                "Which feedback to mark as done?",
                choices=entry_choices,
                use_arrow_keys=True
            ).ask()
            
            if not entry_choice:
                continue
            
            # Extract original index
            index = int(entry_choice.split(']')[0][1:])
            
            # Select status (only implemented or dismissed, as those archive)
            status_choice = questionary.select(
                "Mark as:",
                choices=["✓ Implemented (archive)", "✕ Dismissed (archive)", "Cancel"],
                use_arrow_keys=True
            ).ask()
            
            if status_choice and status_choice != "Cancel":
                if "Implemented" in status_choice:
                    storage.update_feedback_status(index, 'implemented')
                    storage.archive_feedback(index)
                    console.print(f"[green]✓ Feedback #{index} marked as implemented and archived![/green]")
                elif "Dismissed" in status_choice:
                    storage.update_feedback_status(index, 'dismissed')
                    storage.archive_feedback(index)
                    console.print(f"[yellow]✕ Feedback #{index} dismissed and archived.[/yellow]")
        
        elif choice.startswith("["):
            # User selected a specific feedback entry to view
            try:
                index = int(choice.split(']')[0][1:])
                if 0 <= index < len(entries):
                    show_feedback_detail(entries[index], index, console)
                    console.print("\n[dim]Press Enter to continue...[/dim]")
                    input()
            except (ValueError, IndexError):
                console.print("[red]Error displaying feedback[/red]")


def main():
    """Main feedback viewer workflow."""
    console = Console()
    
    # Print header
    console.print(Panel.fit(
        f"[bold magenta]Feedback Viewer[/bold magenta]\n"
        f"[dim]Review tool improvement suggestions[/dim]",
        border_style="magenta"
    ))
    
    try:
        # Initialize storage
        storage = Storage()
        
        # Interactive menu
        interactive_menu(storage, console)
        
        console.print("\n[dim]Goodbye![/dim]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
