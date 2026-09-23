# TIL — Today I Learned

Short notes on things I learn while building software: Django, PostgreSQL,
Flutter, AI/RAG, security, and whatever else comes up.

Entries live in `data/entries.json` and are managed with a small CLI:

```bash
python crud.py create --title "Postgres row-level security" --body "..."
python crud.py list
python crud.py get <id>
python crud.py update <id> --body "..."
python crud.py delete <id>
```

A GitHub Action (`.github/workflows/daily-commit.yml`) runs once a day and
records a daily log entry.
