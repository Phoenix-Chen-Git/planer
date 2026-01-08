"""Configuration loader for daily planning tool."""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv


class ConfigLoader:
    """Handles loading and accessing configuration from config.yaml and .env files."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the config loader.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config = None
        self._load_env()
        self._load_config()
    
    def _load_env(self):
        """Load environment variables from .env file."""
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            print(f"⚠️  Warning: .env file not found at {env_path}")
            print("   Copy .env.example to .env and add your DeepSeek API key")
    
    def _load_config(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def get_daily_jobs(self) -> list:
        """Get the list of daily job templates.
        
        Returns:
            List of job dictionaries with 'name' and 'description'
        """
        return self.config.get('daily_jobs', [])
    
    def get_deepseek_config(self) -> dict:
        """Get DeepSeek API configuration.
        
        Returns:
            Dictionary with DeepSeek settings
        """
        return self.config.get('deepseek', {})
    
    def get_api_key(self) -> str:
        """Get DeepSeek API key from environment variables.
        
        Returns:
            API key string
        
        Raises:
            ValueError: If API key is not set
        """
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key or api_key == 'your_api_key_here':
            raise ValueError(
                "DEEPSEEK_API_KEY not set. "
                "Please copy .env.example to .env and add your API key."
            )
        return api_key
    
    def get_preferences(self) -> dict:
        """Get user preferences.
        
        Returns:
            Dictionary with user preferences
        """
        return self.config.get('preferences', {})


def load_config(config_path: str = "config.yaml") -> ConfigLoader:
    """Convenience function to load configuration.
    
    Args:
        config_path: Path to the YAML configuration file
    
    Returns:
        ConfigLoader instance
    """
    return ConfigLoader(config_path)
