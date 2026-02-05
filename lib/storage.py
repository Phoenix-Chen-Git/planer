"""Data storage utilities for daily plans and logs."""
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List


def migrate_to_user_directory():
    """Migrate data from project directory to user directory on first run."""
    home = Path.home()
    user_data_dir = home / ".daily_planner" / "data"

    # If user directory already exists, no migration needed
    if user_data_dir.exists():
        return

    # Find project directory (where this script is located)
    project_dir = Path(__file__).parent.parent / "data"

    if not project_dir.exists():
        # No data to migrate, create fresh directory
        user_data_dir.mkdir(parents=True, exist_ok=True)
        return

    # Copy entire data directory
    import shutil
    print(f"📦 Migrating data from {project_dir} to {user_data_dir}...")
    shutil.copytree(project_dir, user_data_dir)
    print(f"✅ Migration complete!")


class Storage:
    """Handles saving and loading daily plans and logs."""
    
    def __init__(self, data_dir: str = None):
        """Initialize storage.

        Args:
            data_dir: Directory to store data files (defaults to ~/.daily_planner/data)
        """
        if data_dir is None:
            # Use user's home directory
            home = Path.home()
            data_dir = home / ".daily_planner" / "data"

            # Migrate data on first run
            migrate_to_user_directory()

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    def save_log(self, log_data: Dict[str, Any], date: Optional[datetime] = None) -> None:
        """Save daily log.
        
        Args:
            log_data: Log data dictionary
            date: Date for the log, defaults to today
        """
        json_path = self.get_log_path(date)
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
    

    
    def get_radar_path(self) -> Path:
        """Get path for personal radar data file.
        
        Returns:
            Path to radar.json
        """
        return self.data_dir / "radar.json"
        
    def load_radar(self) -> Dict[str, Any]:
        """Load personal radar data.
        
        Returns:
            Dictionary containing 'current' (abilities) and 'history' (checkpoints)
        """
        radar_path = self.get_radar_path()
        
        if not radar_path.exists():
            return {'current': {'abilities': []}, 'history': []}
            
        with open(radar_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Migration: If it's the old format (directly has "abilities"), nest it under "current"
        if "abilities" in data and "current" not in data:
            data = {
                "current": {"abilities": data["abilities"]},
                "history": []
            }
            # Save migrated structure
            with open(radar_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        return data
            
    def save_radar(self, radar_data: Dict[str, Any]) -> None:
        """Save personal radar data (current state).
        
        Args:
            radar_data: Dictionary containing 'current' state (abilities)
        """
        radar_path = self.get_radar_path()
        
        # Load existing to preserve history
        existing = self.load_radar()
        
        # Update current state
        # Support both full structure or just the 'abilities' wrapper
        if "abilities" in radar_data:
             existing['current'] = radar_data
        elif "current" in radar_data:
             existing['current'] = radar_data['current']
        
        with open(radar_path, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
            
    def save_radar_checkpoint(self) -> Dict[str, Any]:
        """Save the current radar state as a history checkpoint.
        
        Returns:
            The created checkpoint object
        """
        data = self.load_radar()
        current = data.get('current', {})
        
        checkpoint = {
            "date": datetime.now().isoformat(),
            "abilities": current.get('abilities', [])
        }
        
        if 'history' not in data:
            data['history'] = []
            
        data['history'].append(checkpoint)
        
        radar_path = self.get_radar_path()
        with open(radar_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        return checkpoint

    def get_feedback_path(self) -> Path:
        """Get path for centralized feedback file.
        
        Returns:
            Path to tool_feedback.json
        """
        return self.data_dir / "tool_feedback.json"
    

    
    def load_all_feedback(self) -> Dict[str, Any]:
        """Load all feedback entries.
        
        Returns:
            Dictionary containing all feedback entries, or empty structure if none exists
        """
        feedback_path = self.get_feedback_path()
        
        if not feedback_path.exists():
            return {'feedback_entries': []}
        
        with open(feedback_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Migration: Ensure all entries have IDs
        modified = False
        import uuid
        for entry in data.get('feedback_entries', []):
            if 'id' not in entry:
                entry['id'] = str(uuid.uuid4())[:8]
                modified = True
        
        if modified:
            with open(feedback_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        return data
        
    def save_feedback(self, feedback_entry: Dict[str, Any]) -> None:
        """Save a new feedback entry.
        
        Args:
            feedback_entry: Feedback entry to save
        """
        import uuid
        if 'id' not in feedback_entry:
            feedback_entry['id'] = str(uuid.uuid4())[:8]
            
        feedback_data = self.load_all_feedback()
        if 'feedback_entries' not in feedback_data:
            feedback_data['feedback_entries'] = []
            
        feedback_data['feedback_entries'].append(feedback_entry)
        
        feedback_path = self.get_feedback_path()
        with open(feedback_path, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)
    
    def update_feedback_status(self, feedback_id: str, status: str) -> bool:
        """Update status of a feedback entry by ID.
        
        Args:
            feedback_id: ID of feedback entry to update
            status: New status ('pending', 'implemented', 'dismissed')
            
        Returns:
            True if found and updated, False otherwise
        """
        feedback_data = self.load_all_feedback()
        entries = feedback_data.get('feedback_entries', [])
        
        # Find by ID
        target = None
        for entry in entries:
            if str(entry.get('id')) == str(feedback_id):
                target = entry
                break
        
        # Fallback for old index-based calls (if any remain) (actually better to fail or handle upstream)
        # But let's assume we strictly use IDs now
        
        if target:
            target['status'] = status
            feedback_path = self.get_feedback_path()
            with open(feedback_path, 'w', encoding='utf-8') as f:
                json.dump(feedback_data, f, indent=2, ensure_ascii=False)
            return True
            
        return False
        
    def delete_feedback(self, feedback_id: str) -> Optional[Dict]:
        """Delete a feedback entry by ID.
        
        Args:
            feedback_id: ID to delete
            
        Returns:
            Deleted entry or None if not found
        """
        feedback_data = self.load_all_feedback()
        entries = feedback_data.get('feedback_entries', [])
        
        target_idx = -1
        for i, entry in enumerate(entries):
            if str(entry.get('id')) == str(feedback_id):
                target_idx = i
                break
        
        if target_idx >= 0:
            deleted = entries.pop(target_idx)
            feedback_path = self.get_feedback_path()
            with open(feedback_path, 'w', encoding='utf-8') as f:
                json.dump(feedback_data, f, indent=2, ensure_ascii=False)
            return deleted
            
        return None
    
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
    
    def get_today_stats(self) -> Dict[str, int]:
        """Get task completion stats for today.
        
        Returns:
            Dict with 'completed', 'quit', 'pending', 'total' counts
        """
        plan = self.load_plan()
        if not plan:
            return {'completed': 0, 'quit': 0, 'pending': 0, 'total': 0}
        
        completion = plan.get('completion_status', {})
        jobs = plan.get('jobs', [])
        
        # Count tasks recursively
        def count_tasks(job_list):
            completed = quit_count = pending = 0
            for job in job_list:
                job_name = job.get('name') or job.get('task_name', 'Unknown')
                status = completion.get(job_name)
                
                if status == 'done' or status is True:
                    completed += 1
                elif status == 'quit':
                    quit_count += 1
                else:
                    pending += 1
                
                # Count sub-jobs
                sub_jobs = job.get('sub_jobs', [])
                if sub_jobs:
                    sub_stats = count_tasks(sub_jobs)
                    completed += sub_stats[0]
                    quit_count += sub_stats[1]
                    pending += sub_stats[2]
            
            return completed, quit_count, pending
        
        completed, quit_count, pending = count_tasks(jobs)
        total = completed + quit_count + pending
        
        return {
            'completed': completed,
            'quit': quit_count,
            'pending': pending,
            'total': total
        }
    
    def calculate_streak(self) -> int:
        """Calculate consecutive days with at least one completed task.
        
        Returns:
            Number of consecutive days (streak)
        """
        streak = 0
        current_date = datetime.now()
        
        # Check each day going backwards
        while True:
            plan = self.load_plan(current_date)
            
            if not plan:
                # No plan for this day, streak broken
                break
            
            completion = plan.get('completion_status', {})
            
            # Check if any task was completed (done or quit counts as resolved)
            has_completed = any(
                status == 'done' or status is True
                for status in completion.values()
            )
            
            if has_completed:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                # No completed tasks this day
                break
        
        return streak
    
    def get_available_plan_dates(self) -> list:
        """Get list of all available plan dates.

        Returns:
            List of date strings (YYYY-MM-DD format), sorted descending
        """
        plan_files = sorted(self.data_dir.glob("*-plan.json"), reverse=True)
        dates = []
        for f in plan_files:
            date_str = f.stem.replace("-plan", "")
            dates.append(date_str)
        return dates

    def get_upcoming_tasks(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get tasks from upcoming days.

        Args:
            days: Number of days to look ahead (default: 7)

        Returns:
            List of dicts with 'date', 'date_str', 'job_name', 'task_description', 'is_subtask'
        """
        upcoming = []
        today = datetime.now().date()

        for day_offset in range(1, days + 1):
            future_date = datetime.now() + timedelta(days=day_offset)
            plan = self.load_plan(future_date)

            if not plan:
                continue

            completion = plan.get('completion_status', {})
            jobs = plan.get('jobs', [])

            # Extract incomplete tasks recursively
            def extract_tasks(job_list, parent_name=None):
                tasks = []
                for job in job_list:
                    job_name = job.get('name') or job.get('task_name', 'Unknown')
                    status = completion.get(job_name)

                    # Only include pending tasks (not done or quit)
                    if status != 'done' and status is not True and status != 'quit':
                        task_info = {
                            'date': future_date,
                            'date_str': future_date.strftime("%Y-%m-%d"),
                            'job_name': job_name,
                            'task_description': job.get('user_input', job.get('description', '')),
                            'is_subtask': parent_name is not None,
                            'parent_name': parent_name
                        }
                        tasks.append(task_info)

                    # Check sub-jobs
                    sub_jobs = job.get('sub_jobs', [])
                    if sub_jobs:
                        tasks.extend(extract_tasks(sub_jobs, job_name))

                return tasks

            upcoming.extend(extract_tasks(jobs))

        return upcoming

