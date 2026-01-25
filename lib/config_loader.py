"""Configuration loader for daily planning tool."""
import os
import yaml
from pathlib import Path
from dotenv import load_dotenv


class ConfigLoader:
    """Handles loading and accessing configuration from config.yaml and .env files."""
    
    def __init__(self, config_path: str = None):
        """Initialize the config loader.

        Args:
            config_path: Path to the YAML configuration file
        """
        if config_path is None:
            # Try user config directory first
            home = Path.home()
            user_config = home / ".daily_planner" / "config.yaml"

            if user_config.exists():
                config_path = user_config
            else:
                # Fallback to package directory
                config_path = Path(__file__).parent.parent / "config.yaml"

                # Copy default config to user directory on first run
                if not user_config.parent.exists():
                    user_config.parent.mkdir(parents=True, exist_ok=True)
                if not user_config.exists() and Path(config_path).exists():
                    import shutil
                    print(f"📋 Copying default config to {user_config}")
                    shutil.copy(config_path, user_config)
                    config_path = user_config

        self.config_path = Path(config_path)
        self.config = None
        self._load_env()
        self._load_config()
    
    def _load_env(self):
        """Load environment variables from .env file."""
        home = Path.home()
        user_env = home / ".daily_planner" / ".env"

        # Try user directory first
        if user_env.exists():
            load_dotenv(user_env)
            return

        # Fallback to package directory
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            print(f"⚠️  Warning: .env file not found")
            print(f"   Create {user_env} or {env_path} with your DeepSeek API key")
    
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


def load_config(config_path: str = None) -> ConfigLoader:
    """Convenience function to load configuration.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        ConfigLoader instance
    """
    return ConfigLoader(config_path)
