#!/usr/bin/env python3
"""Morning planning script - helps create daily plans with DeepSeek AI."""
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.config_loader import load_config
from lib.deepseek_client import DeepSeekClient
from lib.storage import Storage
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
import questionary


def collect_sub_jobs(console, parent_name: str, depth: int = 1) -> list:
    """Recursively collect sub-jobs for a parent job.
    
    Args:
        console: Rich console for output
        parent_name: Name of the parent job
        depth: Current nesting depth (for indentation)
    
    Returns:
        List of sub-job dictionaries
    """
    sub_jobs = []
    indent = "  " * depth
    
    while True:
        has_sub = questionary.select(
            f"{indent}Add a sub-task for '{parent_name}'?",
            choices=["Yes", "No"],
            use_arrow_keys=True
        ).ask()
        
        if has_sub == "No":
            break
        
        sub_name = Prompt.ask(f"{indent}[cyan]Sub-task name[/cyan]")
        if not sub_name.strip():
            continue
            
        sub_description = Prompt.ask(f"{indent}[dim]What do you need to do for this[/dim]")
        
        sub_job = {
            'name': sub_name,
            'description': sub_description,
            'sub_jobs': []
        }
        
        # Recursively collect sub-sub-jobs
        sub_job['sub_jobs'] = collect_sub_jobs(console, sub_name, depth + 1)
        
        sub_jobs.append(sub_job)
        console.print(f"{indent}[green]✓ Added sub-task: {sub_name}[/green]")
    
    return sub_jobs


def get_previous_plan(storage: Storage) -> Optional[Dict]:
    """Get yesterday's plan if it exists.
    
    Args:
        storage: Storage instance
        
    Returns:
        Yesterday's plan data or None
    """
    yesterday = datetime.now() - timedelta(days=1)
    return storage.load_plan(yesterday)


def get_unfinished_tasks(plan_data: Dict) -> List[Dict]:
    """Extract tasks that weren't completed.
    
    Args:
        plan_data: Plan data dictionary
        
    Returns:
        List of unfinished job dictionaries
    """
    completion = plan_data.get('completion_status', {})
    jobs = plan_data.get('jobs', [])
    unfinished = []
    
    for job in jobs:
        job_name = job.get('name', '')
        # Check if task was not completed
        if not completion.get(job_name, False):
            unfinished.append(job)
    
    return unfinished


def select_tasks_to_carry_over(unfinished_tasks: List[Dict], console: Console) -> List[Dict]:
    """Let user select which tasks to carry over.
    
    Args:
        unfinished_tasks: List of unfinished tasks
        console: Rich console
        
    Returns:
        List of selected tasks to carry over
    """
    if not unfinished_tasks:
        return []
    
    console.print(f"\n[yellow]Found {len(unfinished_tasks)} unfinished task(s) from yesterday:[/yellow]")
    
    # Build choices for checkbox selection
    from questionary import checkbox
    
    choices = [task['name'] for task in unfinished_tasks]
    
    selected_names = checkbox(
        "Select tasks to carry over (Space to select, Enter to confirm):",
        choices=choices
    ).ask()
    
    if not selected_names:
        return []
    
    # Return selected tasks
    selected_tasks = [task for task in unfinished_tasks if task['name'] in selected_names]
    
    # Mark tasks as carried over
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    for task in selected_tasks:
        task['carried_over_from'] = yesterday_str
        task['original_user_input'] = task.get('user_input', '')
    
    return selected_tasks


def main():
    """Main planning workflow."""
    console = Console()
    
    # Print header
    console.print(Panel.fit(
        f"[bold cyan]Daily Planning Tool[/bold cyan]\n"
        f"[dim]{datetime.now().strftime('%A, %B %d, %Y')}[/dim]",
        border_style="cyan"
    ))
    
    try:
        # Load configuration
        console.print("\n[yellow]Loading configuration...[/yellow]")
        config = load_config()
        
        # Initialize storage
        storage = Storage()
        
        # Check if plan already exists
        if storage.plan_exists():
            console.print("\n[yellow]⚠️  A plan already exists for today.[/yellow]")
            overwrite = questionary.select(
                "Do you want to create a new plan?",
                choices=["Yes", "No"],
                use_arrow_keys=True
            ).ask()
            if overwrite != "Yes":
                console.print("[dim]Exiting...[/dim]")
                return
        
        # Get daily jobs from config
        daily_jobs = config.get_daily_jobs()
        
        if not daily_jobs:
            console.print("[red]No daily jobs found in config.yaml[/red]")
            return
        
        # Initialize DeepSeek client early for optional job chats
        console.print("[yellow]Connecting to DeepSeek AI...[/yellow]")
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
        
        # Check for previous day's unfinished tasks
        console.print("\n[yellow]Checking for unfinished tasks from yesterday...[/yellow]")
        previous_plan = get_previous_plan(storage)
        carried_over_tasks = []
        
        if previous_plan:
            unfinished_tasks = get_unfinished_tasks(previous_plan)
            if unfinished_tasks:
                carried_over_tasks = select_tasks_to_carry_over(unfinished_tasks, console)
                if carried_over_tasks:
                    console.print(f"[green]✓ Carrying over {len(carried_over_tasks)} task(s)[/green]\n")
            else:
                console.print("[green]✓ All tasks from yesterday were completed![/green]\n")
        else:
            console.print("[dim]No plan found for yesterday.[/dim]\n")
        
        # Collect user inputs
        console.print("[bold green]Let's plan your day![/bold green]")
        console.print("[dim]For each category, describe what you want to accomplish.[/dim]\n")
        
        jobs_input = []
        for job in daily_jobs:
            console.print(f"[bold cyan]{job['name']}[/bold cyan]")
            console.print(f"[dim]{job['description']}[/dim]")
            
            user_input = Prompt.ask(f"What do you need to do")
            
            if user_input.strip():
                job_data = {
                    'name': job['name'],
                    'description': job['description'],
                    'user_input': user_input,
                    'sub_jobs': [],
                    'chat_notes': []
                }
                
                # Collect sub-jobs recursively
                job_data['sub_jobs'] = collect_sub_jobs(console, job['name'])
                
                # Optional chat about this job
                want_chat = questionary.select(
                    f"Chat with DeepSeek about '{job['name']}'?",
                    choices=["Yes", "No"],
                    use_arrow_keys=True
                ).ask()
                
                if want_chat == "Yes":
                    console.print("  [dim]Chat about this job. Type 'done' when finished.[/dim]")
                    chat_history = [
                        {"role": "system", "content": f"You are helping the user plan their '{job['name']}' tasks. They want to do: {user_input}. Help them think through this task, offer suggestions, or answer questions. Be concise and helpful."}
                    ]
                    
                    while True:
                        user_msg = Prompt.ask("  [cyan]You[/cyan]")
                        
                        if user_msg.lower() in ['done', 'exit', 'quit', 'q']:
                            console.print("  [dim]Ending chat for this job...[/dim]")
                            break
                        
                        if not user_msg.strip():
                            continue
                        
                        response, chat_history = client.chat(user_msg, chat_history)
                        job_data['chat_notes'].append({
                            'user': user_msg,
                            'assistant': response
                        })
                        
                        console.print(Panel(
                            Markdown(response),
                            title="  [bold magenta]DeepSeek[/bold magenta]",
                            border_style="magenta"
                        ))
                
                jobs_input.append(job_data)
            
            console.print()
        
        if not jobs_input:
            console.print("[yellow]No inputs provided. Exiting...[/yellow]")
            return
        
        # Add carried-over tasks to jobs_input
        if carried_over_tasks:
            console.print(f"\n[cyan]Adding {len(carried_over_tasks)} carried-over task(s) to today's plan...[/cyan]")
            jobs_input.extend(carried_over_tasks)
        
        
        # Generate plan
        console.print("[yellow]Generating your daily plan...[/yellow]\n")
        plan_content = client.generate_plan(jobs_input)
        
        # Refinement loop
        refinement_history = []
        while True:
            # Display plan
            console.print(Panel(
                Markdown(plan_content),
                title="[bold green]Your Daily Plan[/bold green]",
                border_style="green"
            ))
            
            # Ask for feedback
            console.print()
            want_refinement = questionary.select(
                "Do you want to refine this plan?",
                choices=["Yes", "No"],
                use_arrow_keys=True
            ).ask()
            
            if want_refinement != "Yes":
                break
            
            # Get feedback
            feedback = Prompt.ask("[cyan]What would you like to change or add?[/cyan]")
            
            if not feedback.strip():
                console.print("[yellow]No feedback provided, keeping current plan.[/yellow]")
                break
            
            # Refine plan with feedback
            console.print("[yellow]Refining your plan...[/yellow]\n")
            
            refinement_history.append({
                'feedback': feedback,
                'previous_plan': plan_content
            })
            
            # Build refinement prompt
            refine_prompt = f"Here is the current daily plan:\n\n{plan_content}\n\n"
            refine_prompt += f"User feedback: {feedback}\n\n"
            refine_prompt += "Please update the plan based on the feedback. Keep the same structure and format. "
            refine_prompt += "Make the requested changes while preserving what works well."
            
            response = client.client.chat.completions.create(
                model=client.model,
                messages=[
                    {"role": "system", "content": "You are a helpful planning assistant that refines daily plans based on user feedback."},
                    {"role": "user", "content": refine_prompt}
                ],
                temperature=client.temperature_planning,
                max_tokens=client.max_tokens
            )
            
            plan_content = response.choices[0].message.content
        
        # Save plan
        plan_data = {
            'date': datetime.now().isoformat(),
            'jobs': jobs_input,
            'plan_content': plan_content,
            'refinement_history': refinement_history
        }
        
        storage.save_plan(plan_data)
        
        console.print(f"\n[green]✓ Plan saved successfully![/green]")
        console.print(f"[dim]JSON: {storage.get_plan_path()}[/dim]")
        
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Please set up your .env file with your DeepSeek API key.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
