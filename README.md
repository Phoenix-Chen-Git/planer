# 📅 Daily Planner & Logger

A powerful CLI tool powered by **DeepSeek AI** that helps you plan your day in the morning and reflect on it in the evening.

---

## ✨ Features

### 🌅 Morning Planning (`plan.py`)
- **Customizable job categories** from config file
- **Hierarchical sub-tasks** — add sub-jobs recursively (unlimited depth)
- **AI-powered chat** after each job to discuss your plans
- **Smart plan generation** with DeepSeek AI
- **Plan refinement** — iterate until you're satisfied
- **Checkbox format** for easy tracking

### ✅ Task Tracking (`check.py`)
- **Select any day's plan** from history
- **Interactive checklist** with arrow key navigation
- **Mark tasks as done/undone** with visual feedback
- **Progress tracking** with completion percentage
- **Persistent state** saved to JSON

### 📊 Feedback Management (`feedback.py`)
- **View all tool improvement suggestions** in one place
- **Track feedback status** (pending/implemented/dismissed)
- **Interactive commands** to view details and update status
- **Continuous improvement** by reviewing accumulated feedback

### 🌙 Evening Summary (`summarize.py`)
- **Load morning plan** automatically
- **Review each task** with status (yes/no/partial) and quality rating
- **Sub-task review** — recursively review all nested tasks
- **AI chat per task** — discuss what went well or wrong
- **AI-generated summary** of your day
- **Summary refinement** — iterate until satisfied
- **Free chat** with full context of your day
- **Tool reflection** — provide feedback to improve the tool

---

## 🚀 Quick Start

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone https://github.com/Phoenix-Chen-Git/planer.git
cd planer

# Create and activate conda environment
mamba env create -f environment.yml
mamba activate plan_and_log
```

### 2. Install the Tool

```bash
# Install in editable mode (recommended for development)
pip install -e .

# Or regular installation
pip install .
```

This creates CLI commands you can run from anywhere!

### 3. Configure API Key

```bash
# Copy the template
cp .env.example .env

# Edit .env and add your DeepSeek API key
# DEEPSEEK_API_KEY=sk-your-api-key-here
```

> 💡 Get your API key at [platform.deepseek.com](https://platform.deepseek.com)

### 4. Customize Your Jobs (Optional)

Edit `config.yaml` to match your daily routine:

```yaml
daily_jobs:
  - name: "Morning Exercise"
    description: "Physical activity to start the day"
  - name: "Work Tasks"
    description: "Professional responsibilities"
  - name: "Learning"
    description: "Study or skill development"
  - name: "Personal Projects"
    description: "Side projects or hobbies"
```

---

## 📖 Usage

### Installed CLI Commands (After pip install)

After installing, you can use these simple commands from anywhere:

```bash
daily              # Open interactive menu (recommended)
daily-plan         # Go directly to planning
daily-check        # Go directly to task checker
daily-summarize    # Go directly to summary
daily-feedback     # Go directly to feedback viewer
```

**Main menu workflow:**
```bash
daily
```

Use arrow keys to navigate:
1. 🌅 Plan my day (morning)
2. ✅ Check tasks (anytime)
3. 🌙 Summarize my day (evening)
4. 📊 View feedback (anytime)
5. ❌ Exit

---

### Without Installation (Use Python Scripts)

```bash
python daily.py
```

This opens an interactive menu where you can:
1. 🌅 Plan your day (morning)
2. ✅ Check tasks (anytime)
3. 🌙 Summarize your day (evening)
4. 📊 View feedback (anytime)
5. ❌ Exit

Just choose a number and the tool guides you through the rest!

---

If you haven't installed with pip, you can still run scripts directly:

### Morning: Create Your Plan

```bash
python plan.py
```

**Workflow:**
1. For each job category, describe what you want to do
2. Optionally add sub-tasks (nested as deep as you want)
3. Optionally chat with AI about each job
4. AI generates your daily plan with checkboxes
5. Refine the plan if needed
6. Plan is saved to `data/` folder

### Evening: Review & Summarize

```bash
python summarize.py
```

**Workflow:**
1. Your morning plan is displayed
2. Review each task: Did you finish? How did it go?
3. Review sub-tasks recursively
4. Optionally chat about each task
5. AI generates your daily summary
6. Refine the summary if needed
7. Chat freely about your day
8. Provide feedback on the tool (optional) — saved to central feedback storage
9. Summary is saved to `data/` folder

### Anytime: Check Tasks

```bash
python check.py
```

**Workflow:**
1. Select a plan from history (today or past days)
2. View plan and task list
3. Use arrow keys to navigate and mark tasks as done
4. Progress is saved to JSON

### Anytime: Review Feedback

```bash
python feedback.py
```

**Workflow:**
1. View table of all feedback entries
2. Use `v [number]` to view details of specific feedback
3. Use `m [number] done` to mark feedback as implemented
4. Track continuous improvement over time

---

## ⚙️ Configuration

### `config.yaml`

```yaml
daily_jobs:
  - name: "Job Name"
    description: "What this job category covers"

deepseek:
  model: "deepseek-chat"
  temperature_planning: 0      # Focused, deterministic for plans/summaries
  temperature_chat: 0.7        # Creative for conversations
  max_tokens: 2000
  api_base: "https://api.deepseek.com"

preferences:
  timezone: "Asia/Shanghai"
  language: "en"
```

### Temperature Settings

| Setting | Value | Use Case |
|---------|-------|----------|
| `temperature_planning` | 0 | Task lists, summaries — focused & consistent |
| `temperature_chat` | 0.7 | Conversations — natural & creative |

---

## 📁 Data Storage

All plans and logs are saved in the `data/` directory as **JSON files only**:

| File | Description |
|------|-------------|
| `2026-01-08-plan.json` | Daily plan with jobs, sub-jobs, and AI-generated content |
| `2026-01-08-log.json` | Full day log with review, summary, and chat history |
| `tool_feedback.json` | Centralized storage for all tool improvement feedback |

---

## 🗂️ Project Structure

```
Plan_and_log/
├── daily.py              # 🌟 Main entry point (start here!)
├── plan.py               # Morning planning script
├── check.py              # Task checker with arrow key navigation
├── summarize.py          # Evening summary script
├── feedback.py           # Feedback viewer and manager
├── config.yaml           # Your daily job templates & settings
├── .env                  # API key (create from .env.example)
├── data/                 # Your plans and logs (JSON only)
└── lib/                  # Core modules
    ├── config_loader.py
    ├── deepseek_client.py
    └── storage.py
```

---

## 💡 Tips

- **Install with pip** — Run `pip install -e .` for CLI commands
- **Use `daily` command** — Simplest way after installation
- **Be specific** — The more detailed your inputs, the better the AI plans
- **Use sub-tasks** — Break complex jobs into smaller pieces
- **Chat when stuck** — AI can help brainstorm or clarify
- **Refine freely** — Don't settle for the first generated plan/summary
- **Review JSON files** — All data is structured and easy to parse
- **Track feedback** — Regular review helps continuous improvement

---

## 🔧 Requirements

- Python 3.8+
- DeepSeek API key
- Conda/Mamba (recommended) or pip

---

## 📄 License

MIT

---

## 🙏 Acknowledgments

Built with:
- [DeepSeek AI](https://deepseek.com) — Powerful language model
- [Rich](https://github.com/Textualize/rich) — Beautiful terminal formatting
- [python-dotenv](https://github.com/theskumar/python-dotenv) — Environment management
