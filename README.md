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

### 2. Configure API Key

```bash
# Copy the template
cp .env.example .env

# Edit .env and add your DeepSeek API key
# DEEPSEEK_API_KEY=sk-your-api-key-here
```

> 💡 Get your API key at [platform.deepseek.com](https://platform.deepseek.com)

### 3. Customize Your Jobs (Optional)

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
8. Provide feedback on the tool (optional)
9. Summary is saved to `data/` folder

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

All plans and logs are saved in the `data/` directory:

| File | Description |
|------|-------------|
| `2026-01-08-plan.json` | Plan data (structured) |
| `2026-01-08-plan.md` | Plan (human-readable) |
| `2026-01-08-log.json` | Full day log with all data |
| `2026-01-08-log.md` | Summary (human-readable) |

---

## 🗂️ Project Structure

```
Plan_and_log/
├── config.yaml          # Your daily job templates & settings
├── .env                  # API key (create from .env.example)
├── .env.example          # API key template
├── environment.yml       # Conda/Mamba environment
├── requirements.txt      # Pip dependencies
├── plan.py               # Morning planning script
├── summarize.py          # Evening summary script
├── data/                 # Your plans and logs
└── lib/
    ├── config_loader.py  # Configuration management
    ├── deepseek_client.py # DeepSeek API client
    └── storage.py        # Data persistence
```

---

## 💡 Tips

- **Be specific** — The more detailed your inputs, the better the AI plans
- **Use sub-tasks** — Break complex jobs into smaller pieces
- **Chat when stuck** — AI can help brainstorm or clarify
- **Refine freely** — Don't settle for the first generated plan/summary
- **Review markdown files** — Great for long-term reflection

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
