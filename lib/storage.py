"""Data storage utilities for daily plans and logs."""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class Storage:
    """Handles saving and loading daily plans and logs."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize storage.
        
        Args:
            data_dir: Directory to store data files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
    
    def _get_date_str(self, date: Optional[datetime] = None) -> str:
        """Get date string in YYYY-MM-DD format.
        
        Args:
            date: Date to format, defaults to today
        
        Returns:
            Date string
        """
        if date is None:
            date = datetime.now()
        return date.strftime("%Y-%m-%d")
    
    def get_plan_path(self, date: Optional[datetime] = None, format: str = "json") -> Path:
        """Get path for plan file.
        
        Args:
            date: Date for the plan, defaults to today
            format: File format ('json' or 'md')
        
        Returns:
            Path to plan file
        """
        date_str = self._get_date_str(date)
        return self.data_dir / f"{date_str}-plan.{format}"
    
    def get_log_path(self, date: Optional[datetime] = None, format: str = "json") -> Path:
        """Get path for log file.
        
        Args:
            date: Date for the log, defaults to today
            format: File format ('json' or 'md')
        
        Returns:
            Path to log file
        """
        date_str = self._get_date_str(date)
        return self.data_dir / f"{date_str}-log.{format}"
    
    def save_plan(self, plan_data: Dict[str, Any], markdown_content: str = None) -> None:
        """Save daily plan.
        
        Args:
            plan_data: Plan data dictionary
            markdown_content: Optional markdown formatted plan
        """
        # Save JSON
        json_path = self.get_plan_path(format="json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(plan_data, f, indent=2, ensure_ascii=False)
        
        # Save markdown if provided
        if markdown_content:
            md_path = self.get_plan_path(format="md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
    
    def load_plan(self, date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """Load daily plan.
        
        Args:
            date: Date for the plan, defaults to today
        
        Returns:
            Plan data dictionary or None if not found
        """
        json_path = self.get_plan_path(date, format="json")
        if not json_path.exists():
            return None
        
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_log(self, log_data: Dict[str, Any], markdown_content: str = None) -> None:
        """Save daily log.
        
        Args:
            log_data: Log data dictionary
            markdown_content: Optional markdown formatted log
        """
        # Save JSON
        json_path = self.get_log_path(format="json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
        
        # Save markdown if provided
        if markdown_content:
            md_path = self.get_log_path(format="md")
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
    
    def load_log(self, date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """Load daily log.
        
        Args:
            date: Date for the log, defaults to today
        
        Returns:
            Log data dictionary or None if not found
        """
        json_path = self.get_log_path(date, format="json")
        if not json_path.exists():
            return None
        
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def plan_exists(self, date: Optional[datetime] = None) -> bool:
        """Check if a plan exists for the given date.
        
        Args:
            date: Date to check, defaults to today
        
        Returns:
            True if plan exists
        """
        return self.get_plan_path(date, format="json").exists()
