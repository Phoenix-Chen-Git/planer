#!/usr/bin/env python3
"""Flask web server for Daily Planner & Logger."""
import sys
import webbrowser
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from flask import Flask, render_template, jsonify, request
from lib.config_loader import load_config
from lib.deepseek_client import DeepSeekClient
from lib.storage import Storage

app = Flask(__name__)
storage = Storage()

# Initialize AI client
try:
    config = load_config()
    deepseek_config = config.get_deepseek_config()
    api_key = config.get_api_key()
    
    ai_client = DeepSeekClient(
        api_key=api_key,
        model=deepseek_config.get('model', 'deepseek-chat'),
        temperature_planning=deepseek_config.get('temperature_planning', 0.0),
        temperature_chat=deepseek_config.get('temperature_chat', 0.7),
        max_tokens=deepseek_config.get('max_tokens', 2000),
        api_base=deepseek_config.get('api_base', 'https://api.deepseek.com')
    )
except Exception as e:
    print(f"Warning: AI client not available: {e}")
    ai_client = None


def get_date_str(date: Optional[datetime] = None) -> str:
    """Get date string in YYYY-MM-DD format."""
    if date is None:
        date = datetime.now()
    return date.strftime("%Y-%m-%d")


def can_plan_today() -> tuple:
    """Check if yesterday's summary exists (only if yesterday had a plan).
    
    Returns:
        Tuple of (can_plan: bool, message: str, yesterday_summary: dict or None)
    """
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_plan = storage.load_plan(yesterday)
    yesterday_log = storage.load_log(yesterday)
    
    # If yesterday had no plan, no summary required - user can plan freely
    if not yesterday_plan:
        return True, "No plan yesterday - ready to start fresh", None
    
    # Yesterday had a plan - check if summary exists
    # A valid summary can be: summary text, reflection, or job_reviews
    if yesterday_log:
        has_summary = (
            yesterday_log.get('summary') or 
            yesterday_log.get('reflection') or 
            len(yesterday_log.get('job_reviews', [])) > 0
        )
        if has_summary:
            return True, "Yesterday's summary completed", yesterday_log
    
    return False, "Please complete yesterday's summary first (you had a plan)", None


def get_contribution_data(weeks: int = 16) -> Dict[str, Dict]:
    """Get contribution calendar data."""
    end_date = datetime.now()
    start_date = end_date - timedelta(weeks=weeks)
    
    contributions = {}
    current = start_date
    
    while current <= end_date:
        date_str = get_date_str(current)
        plan = storage.load_plan(current)
        log = storage.load_log(current)
        
        completed = 0
        total = 0
        has_plan = plan is not None
        
        if log and 'job_reviews' in log:
            for job in log['job_reviews']:
                if job.get('completion_status') == 'done':
                    completed += 1
                total += 1
                for sub in job.get('sub_job_reviews', []):
                    if sub.get('completion_status') == 'done':
                        completed += 1
                    total += 1
        elif plan and 'jobs' in plan:
            for job in plan.get('jobs', []):
                total += 1
                total += len(job.get('sub_jobs', []))
        
        contributions[date_str] = {
            'completed': completed,
            'total': total,
            'has_plan': has_plan
        }
        
        current += timedelta(days=1)
    
    return contributions


# ============ API Routes ============

@app.route('/')
def index():
    """Render main dashboard."""
    return render_template('index.html')


@app.route('/plan')
def plan_page():
    """Render planning page."""
    return render_template('plan.html')


@app.route('/summary')
def summary_page():
    """Render summary page."""
    return render_template('summary.html')


@app.route('/tasks')
def tasks_page():
    """Render tasks page."""
    return render_template('tasks.html')


@app.route('/todos')
def todos_page():
    """Render to-dos page."""
    return render_template('todos.html')


@app.route('/history')
def history_page():
    """Render history page."""
    return render_template('history.html')


@app.route('/feedback')
def feedback_page():
    """Render feedback page."""
    return render_template('feedback.html')


@app.route('/goals')
def goals_page():
    """Render goals page."""
    return render_template('goals.html')


# ============ Goals API ============

from calendar_view import (
    load_goals, save_goals, calculate_time_progress, 
    get_goal_by_id, generate_sub_goal_id, migrate_goals_data
)


@app.route('/api/goals')
def api_get_goals():
    """Get all goals with hierarchy and calculated progress."""
    goals_data = load_goals()
    
    def add_time_progress(goal_or_sub):
        """Add calculated time progress to goal/sub-goal."""
        created = goal_or_sub.get('created_at')
        deadline = goal_or_sub.get('deadline')
        
        if created and deadline:
            goal_or_sub['time_progress'] = calculate_time_progress(created, deadline)
            # Calculate days remaining
            try:
                from datetime import datetime
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                days_remaining = (deadline_date - datetime.now()).days
                goal_or_sub['days_remaining'] = days_remaining
            except:
                goal_or_sub['days_remaining'] = None
        else:
            goal_or_sub['time_progress'] = goal_or_sub.get('progress', 0)
            goal_or_sub['days_remaining'] = None
        
        # Recursively process sub-goals
        for sub in goal_or_sub.get('sub_goals', []):
            add_time_progress(sub)
    
    for goal in goals_data.get('goals', []):
        add_time_progress(goal)
    
    return jsonify(goals_data)


@app.route('/api/goals', methods=['POST'])
def api_add_goal():
    """Create a new goal."""
    data = request.json
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'success': False, 'error': 'Name required'}), 400
    
    goals_data = load_goals()
    
    new_goal = {
        'id': len(goals_data['goals']) + len(goals_data.get('archived', [])) + 1,
        'name': name,
        'type': data.get('type', 'long_term'),
        'priority': data.get('priority', 'medium'),
        'created_at': datetime.now().isoformat(),
        'deadline': data.get('deadline'),
        'status': 'active',
        'progress': 0,
        'sub_goals': [],
        'stages': data.get('stages', {
            'positive': 'Starting with good intentions',
            'negative': 'Facing challenges',
            'current': 'Making progress',
            'improve': 'Building momentum'
        })
    }
    
    goals_data['goals'].append(new_goal)
    save_goals(goals_data)
    
    return jsonify({'success': True, 'goal': new_goal})


@app.route('/api/goals/<goal_id>', methods=['PUT'])
def api_update_goal(goal_id: str):
    """Update a goal or sub-goal."""
    data = request.json
    goals_data = load_goals()
    
    goal = get_goal_by_id(goals_data, goal_id)
    if not goal:
        return jsonify({'success': False, 'error': 'Goal not found'}), 404
    
    # Update allowed fields
    if 'name' in data:
        goal['name'] = data['name']
    if 'deadline' in data:
        goal['deadline'] = data['deadline'] if data['deadline'] else None
    if 'priority' in data:
        goal['priority'] = data['priority']
    if 'status' in data:
        goal['status'] = data['status']
        if data['status'] == 'completed':
            goal['completed_at'] = datetime.now().isoformat()
    
    save_goals(goals_data)
    return jsonify({'success': True, 'goal': goal})


@app.route('/api/goals/<goal_id>', methods=['DELETE'])
def api_delete_goal(goal_id: str):
    """Delete a goal or sub-goal."""
    goals_data = load_goals()
    
    # Check if it's a top-level goal
    parts = str(goal_id).split('.')
    if len(parts) == 1:
        # Top-level goal
        goals_data['goals'] = [g for g in goals_data['goals'] if str(g.get('id')) != goal_id]
    else:
        # Sub-goal - find parent and remove from sub_goals
        parent_id = '.'.join(parts[:-1])
        parent = get_goal_by_id(goals_data, parent_id)
        if parent:
            parent['sub_goals'] = [s for s in parent.get('sub_goals', []) if str(s.get('id')) != goal_id]
    
    save_goals(goals_data)
    return jsonify({'success': True})


@app.route('/api/goals/<parent_id>/subgoals', methods=['POST'])
def api_add_subgoal(parent_id: str):
    """Add a sub-goal to an existing goal."""
    data = request.json
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'success': False, 'error': 'Name required'}), 400
    
    goals_data = load_goals()
    parent = get_goal_by_id(goals_data, parent_id)
    
    if not parent:
        return jsonify({'success': False, 'error': 'Parent goal not found'}), 404
    
    # Check depth limit
    depth = len(str(parent_id).split('.'))
    if depth >= 3:
        return jsonify({'success': False, 'error': 'Maximum nesting depth (3 levels) reached'}), 400
    
    if 'sub_goals' not in parent:
        parent['sub_goals'] = []
    
    new_id = generate_sub_goal_id(parent_id, parent['sub_goals'])
    
    new_subgoal = {
        'id': new_id,
        'name': name,
        'created_at': datetime.now().isoformat(),
        'deadline': data.get('deadline'),
        'status': 'active',
        'sub_goals': []
    }
    
    parent['sub_goals'].append(new_subgoal)
    save_goals(goals_data)
    
    return jsonify({'success': True, 'subgoal': new_subgoal})


@app.route('/api/goals/<goal_id>/status', methods=['PUT'])
def api_update_goal_status(goal_id: str):
    """Update goal status (active/completed/archived)."""
    data = request.json
    status = data.get('status')
    
    if status not in ['active', 'completed', 'archived']:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    
    goals_data = load_goals()
    goal = get_goal_by_id(goals_data, goal_id)
    
    if not goal:
        return jsonify({'success': False, 'error': 'Goal not found'}), 404
    
    goal['status'] = status
    if status == 'completed':
        goal['completed_at'] = datetime.now().isoformat()
    
    save_goals(goals_data)
    return jsonify({'success': True})


@app.route('/api/feedback')
def api_get_feedback():
    """Get all feedback entries."""
    return jsonify(storage.load_all_feedback())


@app.route('/api/feedback', methods=['POST'])
def api_add_feedback():
    """Add a new feedback entry."""
    data = request.json
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'success': False, 'error': 'Content required'}), 400
    
    feedback_entry = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'original_feedback': content,
        'status': 'pending',
        'created_at': datetime.now().isoformat()
    }
    
    storage.save_feedback(feedback_entry)
    return jsonify({'success': True, 'feedback': feedback_entry})


@app.route('/api/feedback/<int:idx>/status', methods=['POST'])
def api_update_feedback_status(idx: int):
    """Update feedback status."""
    data = request.json
    status = data.get('status', 'pending')
    
    if status not in ['pending', 'implemented', 'dismissed']:
        return jsonify({'success': False, 'error': 'Invalid status'}), 400
    
    storage.update_feedback_status(idx, status)
    return jsonify({'success': True})


@app.route('/api/feedback/<int:idx>', methods=['DELETE'])
def api_delete_feedback(idx: int):
    """Delete a feedback entry."""
    feedback_data = storage.load_all_feedback()
    entries = feedback_data.get('feedback_entries', [])
    
    if idx < 0 or idx >= len(entries):
        return jsonify({'success': False, 'error': 'Invalid index'}), 400
    
    deleted = entries.pop(idx)
    
    # Save updated feedback
    feedback_path = storage.get_feedback_path()
    import json
    with open(feedback_path, 'w', encoding='utf-8') as f:
        json.dump(feedback_data, f, indent=2, ensure_ascii=False)
    
    return jsonify({'success': True, 'deleted': deleted.get('original_feedback', '')[:50]})


@app.route('/api/history/<int:year>/<int:month>')
def api_history(year: int, month: int):
    """Get history entries for a given month."""
    import calendar
    
    # Get all days in the month
    _, num_days = calendar.monthrange(year, month)
    entries = []
    
    for day in range(1, num_days + 1):
        date = datetime(year, month, day)
        date_str = date.strftime('%Y-%m-%d')
        
        plan = storage.load_plan(date)
        log = storage.load_log(date)
        
        # Only include if there's a plan or log
        if plan or log:
            entries.append({
                'date': date_str,
                'plan': plan,
                'log': log
            })
    
    return jsonify({'entries': entries})


@app.route('/api/todos')
def api_get_todos():
    """Get all to-dos."""
    todos_data = storage.load_todos()
    return jsonify(todos_data)


@app.route('/api/todos', methods=['POST'])
def api_add_todo():
    """Add a new to-do."""
    data = request.json
    title = data.get('title', '').strip()
    deadline = data.get('deadline')
    
    if not title:
        return jsonify({'success': False, 'error': 'Title required'}), 400
    
    if not deadline:
        return jsonify({'success': False, 'error': 'Deadline required'}), 400
    
    todos_data = storage.load_todos()
    
    new_todo = {
        'id': len(todos_data['todos']),
        'title': title,
        'deadline': deadline,
        'completed': False,
        'created_at': datetime.now().isoformat()
    }
    
    todos_data['todos'].append(new_todo)
    storage.save_todos(todos_data)
    
    return jsonify({'success': True, 'todo': new_todo})


@app.route('/api/todos/<int:idx>/toggle', methods=['POST'])
def api_toggle_todo(idx: int):
    """Toggle to-do completion status."""
    todos_data = storage.load_todos()
    todos = todos_data.get('todos', [])
    
    if idx < 0 or idx >= len(todos):
        return jsonify({'success': False, 'error': 'Invalid index'}), 400
    
    todos[idx]['completed'] = not todos[idx].get('completed', False)
    if todos[idx]['completed']:
        todos[idx]['completed_at'] = datetime.now().isoformat()
    else:
        todos[idx].pop('completed_at', None)
    
    storage.save_todos(todos_data)
    return jsonify({'success': True, 'completed': todos[idx]['completed']})


@app.route('/api/todos/<int:idx>', methods=['DELETE'])
def api_delete_todo(idx: int):
    """Delete a to-do."""
    todos_data = storage.load_todos()
    todos = todos_data.get('todos', [])
    
    if idx < 0 or idx >= len(todos):
        return jsonify({'success': False, 'error': 'Invalid index'}), 400
    
    deleted = todos.pop(idx)
    storage.save_todos(todos_data)
    
    return jsonify({'success': True, 'deleted': deleted['title']})


@app.route('/api/today')
def api_today():
    """Get today's status, plan, and stats."""
    today = datetime.now()
    today_str = get_date_str(today)
    
    plan = storage.load_plan(today)
    log = storage.load_log(today)
    stats = storage.get_today_stats()
    streak = storage.calculate_streak()
    
    can_plan, message, yesterday_summary = can_plan_today()
    
    return jsonify({
        'date': today_str,
        'date_formatted': today.strftime("%A, %B %d, %Y"),
        'time': today.strftime("%I:%M %p"),
        'plan': plan,
        'log': log,
        'stats': stats,
        'streak': streak,
        'workflow': {
            'can_plan': can_plan,
            'message': message,
            'yesterday_summary': yesterday_summary.get('summary') if yesterday_summary else None
        }
    })


@app.route('/api/plan/<date>')
def api_get_plan(date: str):
    """Get plan for specific date."""
    try:
        plan_date = datetime.strptime(date, "%Y-%m-%d")
        plan = storage.load_plan(plan_date)
        return jsonify({'success': True, 'plan': plan})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/plan', methods=['POST'])
def api_create_plan():
    """Create or update daily plan."""
    data = request.json
    
    # Check workflow constraint
    can_plan, message, _ = can_plan_today()
    if not can_plan:
        return jsonify({
            'success': False, 
            'error': message,
            'workflow_blocked': True
        }), 400
    
    try:
        plan_data = {
            'date': datetime.now().isoformat(),
            'jobs': data.get('jobs', []),
            'plan_content': data.get('plan_content', ''),
            'refinement_history': [],
            'completion_status': {}
        }
        storage.save_plan(plan_data)
        return jsonify({'success': True, 'message': 'Plan saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/summary', methods=['POST'])
def api_create_summary():
    """Create summary for a specific date (visible when planning the next day)."""
    data = request.json
    
    try:
        # Use provided date or default to today
        date_str = data.get('date')
        if date_str:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            target_date = datetime.now()
        
        # Get the summary content - use 'summary' field or 'ai_summary' if 'summary' is empty
        summary_content = data.get('summary', '') or data.get('ai_summary', '')
        
        log_data = {
            'date': target_date.isoformat(),
            'job_reviews': data.get('job_reviews', []),
            'summary': summary_content,  # Make sure this field is populated
            'reflection': data.get('reflection', ''),
            'ai_generated_summary': data.get('ai_summary', '')
        }
        
        # Pass the target_date to save_log so it saves to the correct file
        storage.save_log(log_data, target_date)
        
        return jsonify({'success': True, 'message': f'Summary saved for {date_str or "today"}'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/summary/<date>')
def api_get_summary(date: str):
    """Get summary for specific date."""
    try:
        summary_date = datetime.strptime(date, "%Y-%m-%d")
        log = storage.load_log(summary_date)
        return jsonify({'success': True, 'log': log})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/task/toggle', methods=['POST'])
def api_toggle_task():
    """Toggle task completion status."""
    data = request.json
    job_index = data.get('job_index')
    sub_job_index = data.get('sub_job_index')  # None for main job
    path_key = data.get('path_key')  # For nested sub-tasks (e.g., "0_1_2")
    new_status = data.get('status')  # 'done', 'pending', 'quit'
    
    try:
        today = datetime.now()
        plan = storage.load_plan(today)
        
        if not plan:
            return jsonify({'success': False, 'error': 'No plan for today'}), 404
        
        # Update completion status
        if 'completion_status' not in plan:
            plan['completion_status'] = {}
        
        # Determine the key to use
        if path_key is not None:
            key = path_key
        elif sub_job_index is not None:
            key = f"{job_index}_{sub_job_index}"
        else:
            key = str(job_index)
        
        plan['completion_status'][key] = new_status
        storage.save_plan(plan)
        
        return jsonify({'success': True, 'status': new_status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/calendar')
def api_calendar():
    """Get contribution calendar data."""
    weeks = request.args.get('weeks', 16, type=int)
    contributions = get_contribution_data(weeks)
    return jsonify({'contributions': contributions})


@app.route('/api/workflow-check')
def api_workflow_check():
    """Check workflow constraints."""
    can_plan, message, yesterday_summary = can_plan_today()
    return jsonify({
        'can_plan': can_plan,
        'message': message,
        'yesterday_summary': yesterday_summary
    })


@app.route('/api/jobs')
def api_get_jobs():
    """Get configured job categories."""
    try:
        jobs = config.get_daily_jobs()
        return jsonify({'success': True, 'jobs': jobs})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai/plan', methods=['POST'])
def api_ai_plan():
    """Generate AI-assisted plan content."""
    if not ai_client:
        return jsonify({'success': False, 'error': 'AI not available'}), 503
    
    data = request.json
    jobs = data.get('jobs', [])
    
    try:
        # Build prompt
        jobs_list = "\n".join([f"- {job['name']}: {job.get('user_input', '')}" for job in jobs])
        
        messages = [
            {"role": "system", "content": "You are a productivity assistant helping create a focused daily plan."},
            {"role": "user", "content": f"Create a brief, actionable daily plan for these tasks:\n\n{jobs_list}\n\nFormat as markdown with time blocks if appropriate. Keep it concise."}
        ]
        
        ai_content = ai_client.get_completion(messages, use_planning_temp=True)
        return jsonify({'success': True, 'content': ai_content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai/summary', methods=['POST'])
def api_ai_summary():
    """Generate AI-assisted summary."""
    if not ai_client:
        return jsonify({'success': False, 'error': 'AI not available'}), 503
    
    data = request.json
    job_reviews = data.get('job_reviews', [])
    
    try:
        # Build prompt
        reviews_list = []
        for job in job_reviews:
            status = job.get('completion_status', 'pending')
            reviews_list.append(f"- {job['name']}: {status}")
            if job.get('notes'):
                reviews_list.append(f"  Notes: {job['notes']}")
        
        messages = [
            {"role": "system", "content": "You are a productivity coach helping summarize the day."},
            {"role": "user", "content": f"Create a brief reflection on today's work:\n\n{''.join(reviews_list)}\n\nInclude what went well, what could improve, and key learnings. Keep it concise (3-5 sentences)."}
        ]
        
        ai_content = ai_client.get_completion(messages, use_planning_temp=True)
        return jsonify({'success': True, 'content': ai_content})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai/subtasks', methods=['POST'])
def api_ai_subtasks():
    """Generate AI-assisted sub-tasks for a job."""
    if not ai_client:
        return jsonify({'success': False, 'error': 'AI not available'}), 503
    
    data = request.json
    job_name = data.get('job_name', '')
    job_description = data.get('job_description', '')
    
    try:
        messages = [
            {"role": "system", "content": """You are a productivity assistant that breaks down tasks into smaller, actionable sub-tasks.
Rules:
- Generate 3-5 specific, actionable sub-tasks
- Each sub-task should be completable in a short time (15-60 minutes)
- Be specific and concrete, not vague
- Output ONLY a JSON array of strings, no other text
Example output: ["Research topic X", "Draft outline", "Write first section", "Review and edit"]"""},
            {"role": "user", "content": f"Break down this task into sub-tasks:\n\nTask: {job_name}\nDescription: {job_description}"}
        ]
        
        ai_content = ai_client.get_completion(messages, use_planning_temp=True)
        
        # Parse the JSON array from AI response
        import json
        import re
        
        # Try to extract JSON array from response
        json_match = re.search(r'\[.*?\]', ai_content, re.DOTALL)
        if json_match:
            subtasks = json.loads(json_match.group())
        else:
            # Fallback: split by newlines and clean up
            lines = [line.strip().lstrip('- •').strip() for line in ai_content.split('\n') if line.strip()]
            subtasks = [line for line in lines if len(line) > 3][:5]
        
        return jsonify({'success': True, 'subtasks': subtasks})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/task/add-subtasks', methods=['POST'])
def api_add_subtasks():
    """Add sub-tasks to an existing job or nested sub-job."""
    data = request.json
    job_index = data.get('job_index')
    path_key = data.get('path_key')
    subtasks = data.get('subtasks', [])
    
    if job_index is None and path_key is None:
        return jsonify({'success': False, 'error': 'job_index or path_key required'}), 400
    
    if not subtasks:
        return jsonify({'success': False, 'error': 'No subtasks provided'}), 400
    
    try:
        today = datetime.now()
        plan = storage.load_plan(today)
        
        if not plan:
            return jsonify({'success': False, 'error': 'No plan for today'}), 404
        
        jobs = plan.get('jobs', [])
        
        # Find the target (either top-level job or nested sub-job)
        if path_key is not None:
            # path_key is like "0_1_2" meaning jobs[0].sub_jobs[1].sub_jobs[2]
            path_parts = [int(p) for p in path_key.split('_')]
            target = jobs[path_parts[0]]
            
            # Navigate to the nested sub-job
            for part in path_parts[1:]:
                if 'sub_jobs' not in target or part >= len(target['sub_jobs']):
                    return jsonify({'success': False, 'error': 'Invalid path'}), 400
                target = target['sub_jobs'][part]
        else:
            if job_index < 0 or job_index >= len(jobs):
                return jsonify({'success': False, 'error': 'Invalid job index'}), 400
            target = jobs[job_index]
        
        # Initialize sub_jobs if not exists
        if 'sub_jobs' not in target:
            target['sub_jobs'] = []
        
        # Add new sub-tasks
        for subtask in subtasks:
            target['sub_jobs'].append({
                'name': subtask,
                'description': subtask
            })
        
        # Save updated plan
        storage.save_plan(plan)
        
        return jsonify({'success': True, 'message': f'Added {len(subtasks)} sub-tasks'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/task/remove', methods=['POST'])
def api_remove_task():
    """Remove a job from today's plan."""
    data = request.json
    job_index = data.get('job_index')
    
    if job_index is None:
        return jsonify({'success': False, 'error': 'job_index required'}), 400
    
    try:
        today = datetime.now()
        plan = storage.load_plan(today)
        
        if not plan:
            return jsonify({'success': False, 'error': 'No plan for today'}), 404
        
        jobs = plan.get('jobs', [])
        if job_index < 0 or job_index >= len(jobs):
            return jsonify({'success': False, 'error': 'Invalid job index'}), 400
        
        # Remove the job
        removed_job = jobs.pop(job_index)
        
        # Also clean up completion_status for this job and reindex remaining
        old_status = plan.get('completion_status', {})
        new_status = {}
        for key, value in old_status.items():
            if '_' in str(key):
                # Sub-task key like "0_1"
                parts = str(key).split('_')
                parent_idx = int(parts[0])
                if parent_idx < job_index:
                    new_status[key] = value
                elif parent_idx > job_index:
                    # Reindex
                    new_status[f"{parent_idx - 1}_{parts[1]}"] = value
            else:
                # Main task key
                idx = int(key)
                if idx < job_index:
                    new_status[key] = value
                elif idx > job_index:
                    new_status[str(idx - 1)] = value
        
        plan['completion_status'] = new_status
        
        # Save updated plan
        storage.save_plan(plan)
        
        return jsonify({'success': True, 'message': f'Removed {removed_job.get("name", "task")}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def find_available_port(start_port: int = 5050, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port.
    
    Args:
        start_port: Port to start checking from
        max_attempts: Maximum number of ports to try
        
    Returns:
        Available port number
        
    Raises:
        RuntimeError: If no available port found
    """
    import socket
    
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    
    raise RuntimeError(f"No available port found in range {start_port}-{start_port + max_attempts - 1}")


def open_browser(port: int):
    """Open browser after a short delay.
    
    Args:
        port: Port number to open
    """
    import time
    time.sleep(1)
    webbrowser.open(f'http://localhost:{port}')


def main():
    """Main entry point - start web server and open browser."""
    print("\n" + "="*50)
    print("🌅 Daily Planner & Logger - Web UI")
    print("="*50)
    
    # Find available port
    try:
        port = find_available_port()
    except RuntimeError as e:
        print(f"\n❌ Error: {e}")
        print("Please close some applications and try again.")
        return
    
    if port != 5050:
        print(f"\n⚠️  Port 5050 is in use, using port {port} instead")
    
    print(f"\n📍 Starting server at: http://localhost:{port}")
    print("🌐 Opening browser...")
    print("\nPress Ctrl+C to stop the server.\n")
    
    # Open browser in background thread
    browser_thread = threading.Thread(target=lambda: open_browser(port), daemon=True)
    browser_thread.start()
    
    # Start Flask server
    app.run(host='127.0.0.1', port=port, debug=False)


if __name__ == "__main__":
    main()
