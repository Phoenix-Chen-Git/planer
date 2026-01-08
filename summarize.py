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
                'status': status
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
            
            review_data.append(review)
            console.print()
        
        # Initialize DeepSeek client
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
        
        # Generate summary
        console.print("[yellow]Generating your daily summary...[/yellow]\n")
        summary_content = client.generate_summary(plan_data, review_data)
        
        # Display summary
        console.print(Panel(
            Markdown(summary_content),
            title="[bold green]Your Daily Summary[/bold green]",
            border_style="green"
        ))
        
        # Interactive chat
        console.print("\n[bold cyan]Chat with DeepSeek[/bold cyan]")
        console.print("[dim]You can now chat with DeepSeek about your day.[/dim]")
        console.print("[dim]Type 'exit' or 'quit' to finish.[/dim]\n")
        
        chat_history = None
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
        
        # Save log
        log_data = {
            'date': datetime.now().isoformat(),
            'plan': plan_data,
            'review': review_data,
            'summary': summary_content,
            'chat': chat_messages
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
