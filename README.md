# Daily Planning and Logging Tool

A CLI tool powered by DeepSeek AI that helps you plan your day in the morning and reflect on it in the evening.

## Features

- 🌅 **Morning Planning**: Interactive planning session that generates organized daily plans
- 🌙 **Evening Summary**: Review your day and get AI-generated summaries
- 💬 **Chat with AI**: Discuss your day and get insights from DeepSeek
- 📝 **Persistent Storage**: Plans and logs saved in both JSON and Markdown formats
- ⚙️ **Customizable**: Configure your daily job templates in `config.yaml`

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your API key**:
   ```bash
   cp .env.example .env
   # Edit .env and add your DeepSeek API key
   ```

3. **Customize your daily jobs** (optional):
   Edit `config.yaml` to add or modify your daily job categories.

## Usage

### Morning Planning

Run the planning script at the start of your day:

```bash
python plan.py
```

This will:
1. Ask you what you want to accomplish for each job category
2. Send your inputs to DeepSeek AI
3. Generate an organized daily plan with checkboxes
4. Save the plan to `data/YYYY-MM-DD-plan.json` and `.md`

### Evening Summary

Run the summary script at the end of your day:

```bash
python summarize.py
```

This will:
1. Load your morning plan
2. Ask you to review each task (finished? how did it go? what problems?)
3. Generate an AI summary of your day
4. Let you chat with DeepSeek about your day
5. Save everything to `data/YYYY-MM-DD-log.json` and `.md`

## Configuration

### config.yaml

Customize your daily job categories:

```yaml
daily_jobs:
  - name: "Morning Exercise"
    description: "Physical activity to start the day"
  - name: "Work Tasks"
    description: "Professional responsibilities and projects"
  # Add more as needed...
```

### DeepSeek Settings

Adjust AI behavior in `config.yaml`:

```yaml
deepseek:
  model: "deepseek-chat"
  temperature: 0.7  # Higher = more creative, Lower = more focused
  max_tokens: 2000
```

## File Structure

```
Plan_and_log/
├── config.yaml          # Your configuration
├── .env                 # API key (create from .env.example)
├── plan.py              # Morning planning script
├── summarize.py         # Evening summary script
├── data/                # Your plans and logs
│   ├── 2026-01-08-plan.json
│   ├── 2026-01-08-plan.md
│   ├── 2026-01-08-log.json
│   └── 2026-01-08-log.md
└── lib/                 # Library modules
    ├── config_loader.py
    ├── deepseek_client.py
    └── storage.py
```

## Tips

- Run `plan.py` first thing in the morning for best results
- Be specific with your inputs - the AI generates better plans with clear goals
- Use the evening chat to reflect on what worked and what didn't
- Review your markdown files for a readable history of your days

## Requirements

- Python 3.8+
- DeepSeek API key (get one at https://platform.deepseek.com)

## License

MIT
