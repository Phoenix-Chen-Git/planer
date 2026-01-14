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
    
    def get_plan_path(self, date: Optional[datetime] = None) -> Path:
        """Get path for plan file.
        
        Args:
            date: Date for the plan, defaults to today
        
        Returns:
            Path to plan JSON file
        """
        date_str = self._get_date_str(date)
        return self.data_dir / f"{date_str}-plan.json"
    
    def get_log_path(self, date: Optional[datetime] = None) -> Path:
        """Get path for log file.
        
        Args:
            date: Date for the log, defaults to today
        
        Returns:
            Path to log JSON file
        """
        date_str = self._get_date_str(date)
        return self.data_dir / f"{date_str}-log.json"
    
    def save_plan(self, plan_data: Dict[str, Any]) -> None:
        """Save daily plan.
        
        Args:
            plan_data: Plan data dictionary
        """
        json_path = self.get_plan_path()
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(plan_data, f, indent=2, ensure_ascii=False)
    
    def load_plan(self, date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """Load daily plan.
        
        Args:
            date: Date for the plan, defaults to today
        
        Returns:
            Plan data dictionary or None if not found
        """
        json_path = self.get_plan_path(date)
        if not json_path.exists():
            return None
        
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def save_log(self, log_data: Dict[str, Any]) -> None:
        """Save daily log.
        
        Args:
            log_data: Log data dictionary
        """
        json_path = self.get_log_path()
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    def load_log(self, date: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """Load daily log.
        
        Args:
            date: Date for the log, defaults to today
        
        Returns:
            Log data dictionary or None if not found
        """
        json_path = self.get_log_path(date)
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
        return self.get_plan_path(date).exists()
    
    def get_feedback_path(self) -> Path:
        """Get path for centralized feedback file.
        
        Returns:
            Path to tool_feedback.json
        """
        return self.data_dir / "tool_feedback.json"
    
    def save_feedback(self, feedback_entry: Dict[str, Any]) -> None:
        """Save feedback entry to centralized storage.
        
        Args:
            feedback_entry: Feedback entry with date, original_feedback, final_understanding, etc.
        """
        feedback_path = self.get_feedback_path()
        
        # Load existing feedback or create new structure
        if feedback_path.exists():
            with open(feedback_path, 'r', encoding='utf-8') as f:
                feedback_data = json.load(f)
        else:
            feedback_data = {'feedback_entries': []}
        
        # Add new entry
        feedback_data['feedback_entries'].append(feedback_entry)
        
        # Save back
        with open(feedback_path, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)
    
    def load_all_feedback(self) -> Dict[str, Any]:
        """Load all feedback entries.
        
        Returns:
            Dictionary containing all feedback entries, or empty structure if none exists
        """
        feedback_path = self.get_feedback_path()
        
        if not feedback_path.exists():
            return {'feedback_entries': []}
        
        with open(feedback_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def update_feedback_status(self, index: int, status: str) -> None:
        """Update status of a feedback entry.
        
        Args:
            index: Index of feedback entry to update
            status: New status ('pending', 'implemented', 'dismissed')
        """
        feedback_data = self.load_all_feedback()
        
        if 0 <= index < len(feedback_data['feedback_entries']):
            feedback_data['feedback_entries'][index]['status'] = status
            
            feedback_path = self.get_feedback_path()
            with open(feedback_path, 'w', encoding='utf-8') as f:
                json.dump(feedback_data, f, indent=2, ensure_ascii=False)
    
    def get_improves_path(self) -> Path:
        """Get path for archived/implemented feedback directory.
        
        Returns:
            Path to improves directory
        """
        improves_dir = self.data_dir / "improves"
        improves_dir.mkdir(exist_ok=True)
        return improves_dir
    
    def get_archived_feedback_path(self) -> Path:
        """Get path for archived feedback file.
        
        Returns:
            Path to archived_feedback.json
        """
        return self.get_improves_path() / "archived_feedback.json"
    
    def archive_feedback(self, index: int) -> bool:
        """Archive a feedback entry (move to improves directory).
        
        Args:
            index: Index of feedback entry to archive
            
        Returns:
            True if successful
        """
        feedback_data = self.load_all_feedback()
        entries = feedback_data.get('feedback_entries', [])
        
        if not (0 <= index < len(entries)):
            return False
        
        # Get entry to archive
        entry = entries.pop(index)
        entry['archived_date'] = datetime.now().isoformat()
        
        # Load or create archived file
        archived_path = self.get_archived_feedback_path()
        if archived_path.exists():
            with open(archived_path, 'r', encoding='utf-8') as f:
                archived_data = json.load(f)
        else:
            archived_data = {'archived_entries': []}
        
        # Add to archive
        archived_data['archived_entries'].append(entry)
        
        # Save archived
        with open(archived_path, 'w', encoding='utf-8') as f:
            json.dump(archived_data, f, indent=2, ensure_ascii=False)
        
        # Save updated feedback (without archived entry)
        feedback_path = self.get_feedback_path()
        with open(feedback_path, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)
        
        return True
    
    def load_archived_feedback(self) -> Dict[str, Any]:
        """Load all archived feedback entries.
        
        Returns:
            Dictionary containing archived entries
        """
        archived_path = self.get_archived_feedback_path()
        
        if not archived_path.exists():
            return {'archived_entries': []}
        
        with open(archived_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def count_pending_feedback(self) -> int:
        """Count number of pending feedback entries.
        
        Returns:
            Number of pending feedback entries
        """
        feedback_data = self.load_all_feedback()
        entries = feedback_data.get('feedback_entries', [])
        return sum(1 for e in entries if e.get('status', 'pending') == 'pending')
