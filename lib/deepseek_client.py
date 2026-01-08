"""DeepSeek API client for generating plans and summaries."""
from openai import OpenAI
from typing import List, Dict, Any, Optional


class DeepSeekClient:
    """Client for interacting with DeepSeek API."""
    
    def __init__(self, api_key: str, model: str = "deepseek-chat", 
                 temperature_planning: float = 0.0, 
                 temperature_chat: float = 0.7,
                 max_tokens: int = 2000,
                 api_base: str = "https://api.deepseek.com"):
        """Initialize DeepSeek client.
        
        Args:
            api_key: DeepSeek API key
            model: Model name to use
            temperature_planning: Sampling temperature for planning/summary (default: 0.0 for focused)
            temperature_chat: Sampling temperature for chat (default: 0.7 for conversational)
            max_tokens: Maximum tokens in response
            api_base: API base URL
        """
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base
        )
        self.model = model
        self.temperature_planning = temperature_planning
        self.temperature_chat = temperature_chat
        self.max_tokens = max_tokens
    
    def _format_sub_jobs(self, sub_jobs: List[Dict], depth: int = 1) -> str:
        """Recursively format sub-jobs for the prompt.
        
        Args:
            sub_jobs: List of sub-job dictionaries
            depth: Current depth level for indentation
        
        Returns:
            Formatted string of sub-jobs
        """
        if not sub_jobs:
            return ""
        
        indent = "  " * depth
        result = ""
        for sub in sub_jobs:
            result += f"{indent}- Sub-task: {sub['name']}\n"
            result += f"{indent}  What to do: {sub['description']}\n"
            result += self._format_sub_jobs(sub.get('sub_jobs', []), depth + 1)
        return result
    
    def generate_plan(self, jobs_input: List[Dict[str, str]]) -> str:
        """Generate a daily plan from job inputs.
        
        Args:
            jobs_input: List of job dictionaries with 'name', 'description', 'user_input', and optional 'sub_jobs'
        
        Returns:
            Generated plan as markdown with checkboxes
        """
        # Build prompt
        prompt = "You are a helpful assistant that creates organized daily plans.\n\n"
        prompt += "Based on the following job inputs, create a detailed daily plan with checkboxes.\n"
        prompt += "Break down each job into specific, actionable tasks.\n"
        prompt += "Use markdown format with checkbox syntax (- [ ]).\n"
        prompt += "For sub-tasks, use nested indentation to show hierarchy.\n\n"
        
        for job in jobs_input:
            prompt += f"## {job['name']}\n"
            prompt += f"Description: {job['description']}\n"
            prompt += f"What to do: {job['user_input']}\n"
            
            # Add sub-jobs if present
            sub_jobs = job.get('sub_jobs', [])
            if sub_jobs:
                prompt += "Sub-tasks:\n"
                prompt += self._format_sub_jobs(sub_jobs)
            
            prompt += "\n"
        
        prompt += "Please create a well-organized daily plan with clear, actionable tasks. Preserve the hierarchy of sub-tasks."
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful planning assistant that creates clear, actionable daily plans with proper hierarchy."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature_planning,  # Use planning temperature (focused)
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content
    
    def generate_summary(self, plan_data: Dict[str, Any], review_data: List[Dict[str, Any]]) -> str:
        """Generate a summary of the day based on plan and review.
        
        Args:
            plan_data: Original plan data
            review_data: Review responses for each task
        
        Returns:
            Generated summary as markdown
        """
        # Build prompt
        prompt = "You are a thoughtful assistant that helps reflect on daily progress.\n\n"
        prompt += "Based on the following plan and review, create a comprehensive daily summary.\n"
        prompt += "Include accomplishments, challenges, reflections, and recommendations for tomorrow.\n\n"
        
        prompt += "## Original Plan:\n"
        for job in plan_data.get('jobs', []):
            prompt += f"### {job['name']}\n"
            prompt += f"{job['user_input']}\n\n"
        
        prompt += "## Review:\n"
        for review in review_data:
            prompt += f"### {review['job_name']}\n"
            prompt += f"Status: {review['status']}\n"
            if review.get('quality'):
                prompt += f"Quality: {review['quality']}\n"
            if review.get('problem'):
                prompt += f"Issue: {review['problem']}\n"
            prompt += "\n"
        
        prompt += "Please create a thoughtful summary with sections for:\n"
        prompt += "1. Accomplishments\n"
        prompt += "2. Challenges\n"
        prompt += "3. Reflection\n"
        prompt += "4. Recommendations for Tomorrow"
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a thoughtful reflection assistant that helps people learn from their daily experiences."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature_planning,  # Use planning temperature (focused)
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content
    
    def chat(self, message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> tuple[str, List[Dict[str, str]]]:
        """Interactive chat with DeepSeek.
        
        Args:
            message: User message
            conversation_history: Previous conversation messages
        
        Returns:
            Tuple of (response, updated_conversation_history)
        """
        if conversation_history is None:
            conversation_history = [
                {"role": "system", "content": "You are a helpful assistant for daily planning and reflection."}
            ]
        
        # Add user message
        conversation_history.append({"role": "user", "content": message})
        
        # Get response
        response = self.client.chat.completions.create(
            model=self.model,
            messages=conversation_history,
            temperature=self.temperature_chat,  # Use chat temperature (conversational)
            max_tokens=self.max_tokens
        )
        
        assistant_message = response.choices[0].message.content
        
        # Add assistant response to history
        conversation_history.append({"role": "assistant", "content": assistant_message})
        
        return assistant_message, conversation_history
    
    def test_connection(self) -> bool:
        """Test the API connection.
        
        Returns:
            True if connection successful
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False
