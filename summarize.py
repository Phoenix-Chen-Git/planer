#!/usr/bin/env python3
"""Evening summary script - helps review the day and create summaries with DeepSeek AI."""
import sys
from datetime import datetime
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.config_loader import load_config
from lib.deepseek_client import DeepSeekClient
from lib.storage import Storage
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm


def review_sub_jobs(console, sub_jobs: list, depth: int = 1) -> list:
    """Recursively review sub-jobs.
    
    Args:
        console: Rich console for output
        sub_jobs: List of sub-job dictionaries
        depth: Current nesting depth
    
    Returns:
        List of sub-job review data
    """
    if not sub_jobs:
        return []
    
    sub_reviews = []
    indent = "  " * depth
    
    for sub_job in sub_jobs:
        console.print(f"{indent}[cyan]└─ {sub_job['name']}[/cyan]")
        console.print(f"{indent}   [dim]{sub_job['description']}[/dim]")
        
        status = Prompt.ask(
            f"{indent}   Did you finish this?",
            choices=["yes", "no", "partial"],
            default="yes"
        )
        
        review = {
            'task_name': sub_job['name'],
            'status': status,
            'sub_reviews': []
        }
        
        if status == "yes":
            quality = Prompt.ask(
                f"{indent}   How did it go?",
                choices=["excellent", "good", "okay"],
                default="good"
            )
            review['quality'] = quality
        elif status in ["no", "partial"]:
            problem = Prompt.ask(f"{indent}   What was the problem?")
            review['problem'] = problem
        
        # Recursively review sub-sub-jobs
        review['sub_reviews'] = review_sub_jobs(console, sub_job.get('sub_jobs', []), depth + 1)
        
        sub_reviews.append(review)
    
    return sub_reviews


def main():
    """Main summary workflow."""
    console = Console()
    
    # Print header
    console.print(Panel.fit(
        f"[bold magenta]Daily Summary Tool[/bold magenta]\n"
        f"[dim]{datetime.now().strftime('%A, %B %d, %Y')}[/dim]",
        border_style="magenta"
    ))
    
    try:
        # Load configuration
        console.print("\n[yellow]Loading configuration...[/yellow]")
        config = load_config()
        
        # Initialize storage
        storage = Storage()
        
        # Load today's plan
        plan_data = storage.load_plan()
        
        if not plan_data:
            console.print("[red]No plan found for today.[/red]")
            console.print("[yellow]Please run plan.py first to create a daily plan.[/yellow]")
            return
        
        # Display original plan
        console.print("\n[bold cyan]Today's Plan:[/bold cyan]")
        console.print(Panel(
            Markdown(plan_data.get('plan_content', 'No plan content')),
            border_style="cyan"
        ))
        
        # Initialize DeepSeek client early
        console.print("\n[yellow]Connecting to DeepSeek AI...[/yellow]")
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
        
        # Review each job
        console.print("\n[bold green]Let's review your day![/bold green]\n")
        
        review_data = []
        for job in plan_data.get('jobs', []):
            console.print(f"[bold cyan]{job['name']}[/bold cyan]")
            console.print(f"[dim]Planned: {job['user_input']}[/dim]\n")
            
            # Ask completion status
            status = Prompt.ask(
                "Did you finish this?",
                choices=["yes", "no", "partial"],
                default="yes"
            )
            
            review = {
                'job_name': job['name'],
                'status': status,
                'sub_reviews': [],
                'chat_notes': []
            }
            
            if status == "yes":
                quality = Prompt.ask(
                    "How did it go?",
                    choices=["excellent", "good", "okay"],
                    default="good"
                )
                review['quality'] = quality
            elif status in ["no", "partial"]:
                problem = Prompt.ask("What was the problem?")
                review['problem'] = problem
            
            # Review sub-jobs if present
            sub_jobs = job.get('sub_jobs', [])
            if sub_jobs:
                console.print("[dim]Reviewing sub-tasks:[/dim]")
                review['sub_reviews'] = review_sub_jobs(console, sub_jobs)
            
            # Optional chat about this task review
            want_chat = Prompt.ask(
                f"  [yellow]Chat with DeepSeek about '{job['name']}'?[/yellow]",
                choices=["yes", "no"],
                default="no"
            )
            
            if want_chat.lower() == "yes":
                console.print("  [dim]Discuss this task. Type 'done' when finished.[/dim]")
                
                # Build context for this task
                task_context = f"The user planned to work on '{job['name']}: {job['user_input']}'. "
                task_context += f"They reported status: {status}"
                if status == "yes":
                    task_context += f", quality: {review.get('quality', 'N/A')}"
                elif status in ["no", "partial"]:
                    task_context += f", problem: {review.get('problem', 'N/A')}"
                task_context += ". Help them reflect on this task, understand what went well or wrong, or plan improvements."
                
                chat_history = [
                    {"role": "system", "content": task_context}
                ]
                
                while True:
                    user_msg = Prompt.ask("  [cyan]You[/cyan]")
                    
                    if user_msg.lower() in ['done', 'exit', 'quit', 'q']:
                        console.print("  [dim]Ending chat for this task...[/dim]")
                        break
                    
                    if not user_msg.strip():
                        continue
                    
                    response, chat_history = client.chat(user_msg, chat_history)
                    review['chat_notes'].append({
                        'user': user_msg,
                        'assistant': response
                    })
                    
                    console.print(Panel(
                        Markdown(response),
                        title="  [bold magenta]DeepSeek[/bold magenta]",
                        border_style="magenta"
                    ))
            
            review_data.append(review)
            console.print()
        
        # Generate summary
        console.print("[yellow]Generating your daily summary...[/yellow]\n")
        summary_content = client.generate_summary(plan_data, review_data)
        
        # Refinement loop for summary
        refinement_history = []
        while True:
            # Display summary
            console.print(Panel(
                Markdown(summary_content),
                title="[bold green]Your Daily Summary[/bold green]",
                border_style="green"
            ))
            
            # Ask for refinement
            console.print()
            want_refinement = Prompt.ask(
                "[yellow]Do you want to refine this summary?[/yellow]",
                choices=["yes", "no"],
                default="no"
            )
            
            if want_refinement.lower() != "yes":
                break
            
            # Get feedback
            feedback = Prompt.ask("[cyan]What would you like to change or add?[/cyan]")
            
            if not feedback.strip():
                console.print("[yellow]No feedback provided, keeping current summary.[/yellow]")
                break
            
            # Refine summary
            console.print("[yellow]Refining your summary...[/yellow]\n")
            
            refinement_history.append({
                'feedback': feedback,
                'previous_summary': summary_content
            })
            
            # Build refinement prompt
            refine_prompt = f"Here is the current daily summary:\n\n{summary_content}\n\n"
            refine_prompt += f"User feedback: {feedback}\n\n"
            refine_prompt += "Please update the summary based on the feedback. Keep the same structure and format. "
            refine_prompt += "Make the requested changes while preserving what works well."
            
            response = client.client.chat.completions.create(
                model=client.model,
                messages=[
                    {"role": "system", "content": "You are a thoughtful reflection assistant that refines daily summaries based on user feedback."},
                    {"role": "user", "content": refine_prompt}
                ],
                temperature=client.temperature_planning,
                max_tokens=client.max_tokens
            )
            
            summary_content = response.choices[0].message.content
        
        # Interactive chat
        console.print("\n[bold cyan]Chat with DeepSeek[/bold cyan]")
        console.print("[dim]You can now chat with DeepSeek about your day.[/dim]")
        console.print("[dim]Type 'exit' or 'quit' to finish.[/dim]\n")
        
        # Initialize chat with context about the day
        chat_history = [
            {"role": "system", "content": f"You are a helpful assistant for daily reflection. The user has completed their day. Here's their summary:\n\n{summary_content}\n\nHelp them reflect on their day, answer questions, or provide advice."}
        ]
        chat_messages = []
        
        while True:
            user_message = Prompt.ask("[bold cyan]You[/bold cyan]")
            
            if user_message.lower() in ['exit', 'quit', 'q']:
                console.print("[dim]Ending chat session...[/dim]")
                break
            
            if not user_message.strip():
                continue
            
            # Get response
            console.print("[yellow]DeepSeek is thinking...[/yellow]")
            response, chat_history = client.chat(user_message, chat_history)
            
            # Store chat message
            chat_messages.append({
                'user': user_message,
                'assistant': response
            })
            
            # Display response
            console.print(Panel(
                Markdown(response),
                title="[bold magenta]DeepSeek[/bold magenta]",
                border_style="magenta"
            ))
            console.print()
        
        # Tool Reflection
        console.print("\n[bold yellow]📝 Tool Reflection[/bold yellow]")
        console.print("[dim]Help us improve this planning tool![/dim]\n")
        
        tool_feedback = Prompt.ask(
            "[cyan]What do you think this tool can be updated or improved?[/cyan]\n"
            "[dim](Press Enter to skip)[/dim]",
            default=""
        )
        
        tool_reflection = None
        if tool_feedback.strip():
            # Iterative understanding confirmation
            user_description = tool_feedback
            understanding_history = []
            
            while True:
                # DeepSeek summarizes understanding
                console.print("[yellow]DeepSeek is understanding your feedback...[/yellow]\n")
                
                understanding_prompt = f"The user wants to improve a daily planning and logging tool. Their feedback:\n\n{user_description}\n\n"
                understanding_prompt += "Please summarize your understanding of what they want in a clear, concise way. "
                understanding_prompt += "Start with 'I understand that you want...' and be specific about the feature or improvement they're requesting."
                
                response = client.client.chat.completions.create(
                    model=client.model,
                    messages=[
                        {"role": "system", "content": "You are a product manager confirming your understanding of user feedback."},
                        {"role": "user", "content": understanding_prompt}
                    ],
                    temperature=client.temperature_chat,
                    max_tokens=client.max_tokens
                )
                
                ai_understanding = response.choices[0].message.content
                
                console.print(Panel(
                    Markdown(ai_understanding),
                    title="[bold magenta]DeepSeek's Understanding[/bold magenta]",
                    border_style="magenta"
                ))
                
                understanding_history.append({
                    'user_input': user_description,
                    'ai_understanding': ai_understanding
                })
                
                # Ask if user is satisfied
                console.print()
                satisfied = Prompt.ask(
                    "[yellow]Is this understanding correct?[/yellow]",
                    choices=["yes", "no", "refine"],
                    default="yes"
                )
                
                if satisfied.lower() == "yes":
                    console.print("[green]✓ Great! Your feedback has been recorded.[/green]")
                    break
                elif satisfied.lower() == "refine":
                    refinement = Prompt.ask("[cyan]How would you like to refine your description?[/cyan]")
                    if refinement.strip():
                        user_description = refinement
                    else:
                        console.print("[yellow]Keeping current understanding.[/yellow]")
                        break
                else:  # no
                    new_description = Prompt.ask("[cyan]Please describe what you want again[/cyan]")
                    if new_description.strip():
                        user_description = new_description
                    else:
                        console.print("[yellow]Keeping original feedback.[/yellow]")
                        break
            
            tool_reflection = {
                'original_feedback': tool_feedback,
                'understanding_history': understanding_history,
                'final_understanding': ai_understanding
            }
        
        # Save log
        log_data = {
            'date': datetime.now().isoformat(),
            'plan': plan_data,
            'review': review_data,
            'summary': summary_content,
            'refinement_history': refinement_history,
            'chat': chat_messages,
            'tool_reflection': tool_reflection
        }
        
        # Add header to markdown
        date_str = datetime.now().strftime("%Y-%m-%d")
        markdown_content = f"# Daily Summary - {date_str}\n\n{summary_content}\n\n"
        
        if chat_messages:
            markdown_content += "## Chat History\n\n"
            for msg in chat_messages:
                markdown_content += f"**You:** {msg['user']}\n\n"
                markdown_content += f"**DeepSeek:** {msg['assistant']}\n\n"
        
        markdown_content += "---\n*Generated with DeepSeek AI*"
        
        storage.save_log(log_data, markdown_content)
        
        console.print(f"\n[green]✓ Summary saved successfully![/green]")
        console.print(f"[dim]JSON: {storage.get_log_path(format='json')}[/dim]")
        console.print(f"[dim]Markdown: {storage.get_log_path(format='md')}[/dim]")
        
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
