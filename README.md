# Python Project Management CLI Tool

A command-line application for managing users, projects, and tasks. This was my final project for my Python programming course.

## What it does

- Create and manage users
- Add projects to users
- Add tasks to projects and track their status
- Everything saves to a JSON file automatically
- Nice looking tables in the terminal (using the rich library)
- Can parse dates in different formats
- Has tests (using pytest)

## How the code is organized

```
.
├── main.py              # CLI entry point (argparse subcommands)
├── models/
│   ├── person.py        # Base Person class
│   ├── user.py          # User (extends Person) — owns Projects
│   ├── project.py       # Project — owns Tasks, tracks completion %
│   └── task.py          # Task with pending/in_progress/complete lifecycle
├── utils/
│   ├── storage.py       # JSON load/save via Storage class
│   ├── display.py       # Rich-powered terminal output (tables, panels)
│   └── validators.py    # Email and date validation helpers
├── tests/
│   ├── test_models.py   # Unit tests for all model classes
│   └── test_cli.py      # Unit tests for all CLI subcommands
├── data/                # Auto-created; stores users.json at runtime
├── requirements.txt
└── README.md
```

## Setup Instructions

1. Clone or download this repository
2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate        # on Mac/Linux
# venv\Scripts\activate         # on Windows
```
3. Install the required packages:
```bash
pip install -r requirements.txt
```

## How to Run

```bash
python main.py <command> [options]
python main.py --help
python main.py <command> --help
```

### User Commands

```bash
python main.py add-user --name "Alex" --email "alex@example.com"
python main.py list-users
python main.py delete-user --name "Alex"
```

### Project Commands

```bash
python main.py add-project --user "Alex" --title "CLI Tool" \
    --description "Build the CLI" --due-date "2025-12-31"

python main.py list-projects                  # all users
python main.py list-projects --user "Alex"    # filtered

python main.py view-project --title "CLI Tool" --user "Alex"

python main.py update-project --user "Alex" --title "CLI Tool" \
    --description "Updated desc" --due-date "2026-01-01"

python main.py delete-project --user "Alex" --title "CLI Tool"
```

### Task Commands

```bash
python main.py add-task --project "CLI Tool" --title "Write tests" \
    --assigned-to "Alex" --user "Alex"

python main.py list-tasks --project "CLI Tool" --user "Alex"
python main.py start-task    --project "CLI Tool" --task "Write tests" --user "Alex"
python main.py complete-task --project "CLI Tool" --task "Write tests" --user "Alex"
python main.py delete-task   --project "CLI Tool" --task "Write tests" --user "Alex"
```

### Example Usage

```bash
python main.py add-user --name "Alex" --email "alex@example.com"
python main.py add-project --user "Alex" --title "CLI Tool" --due-date "2025-12-31"
python main.py add-task --project "CLI Tool" --title "Implement add-task" --user "Alex"
python main.py add-task --project "CLI Tool" --title "Write tests" --user "Alex"
python main.py start-task    --project "CLI Tool" --task "Implement add-task" --user "Alex"
python main.py complete-task --project "CLI Tool" --task "Implement add-task" --user "Alex"
python main.py view-project  --title "CLI Tool" --user "Alex"
```

## Testing

To run the tests I wrote:

```bash
source venv/bin/activate
pytest tests/ -v
```

## Design Notes

I used object-oriented programming concepts we learned in class:
- **Person** is the base class with name and email
- **User** inherits from Person and can have multiple projects
- **Project** contains multiple tasks and calculates completion percentage
- **Task** has three statuses: pending, in_progress, and complete

## Libraries Used

| Package | Purpose |
|---|---|
| `rich` | Colour-coded tables, panels, status messages in terminal |
| `python-dateutil` | Flexible date string parsing for `--due-date` values |
| `pytest` | Unit testing for models and CLI command handlers |

## How Data is Saved

All data gets saved to `data/users.json` in a nested structure. The file is created automatically when you first add a user. I added error handling for when the file doesn't exist or has bad JSON.

## Things I Know Could Be Better

- Project titles need to be unique per user (but different users can have projects with the same name)
- The --user flag helps when multiple users have projects with the same name
- The JSON file doesn't handle multiple people writing to it at the same time (but that's probably fine for a CLI tool)
- I could have added more features like task priorities or deadlines but ran out of time
