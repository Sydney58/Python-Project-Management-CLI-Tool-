# Python Project Management CLI Tool

This is my final project for my Python programming course. It's a command-line tool for keeping track of users, projects, and tasks. Everything saves to a JSON file so your data sticks around between runs.

I'm actually pretty happy with how it turned out!

## What it does

- Create users and give them projects
- Add tasks to projects and move them through pending → in progress → complete
- See a completion percentage for each project
- Nice coloured tables in the terminal (I used a library called `rich` for this)
- Flexible date input - you can type "Dec 31 2025" instead of having to write "2025-12-31"
- All data saves automatically, nothing gets lost when you close the terminal

## How to Run

```bash
python main.py <command> [options]
python main.py --help               # shows all available commands
python main.py <command> --help     # shows options for a specific command
```

### User Commands

```bash
python main.py add-user --name "Alex" --email "alex@example.com"
python main.py list-users
python main.py delete-user --name "Alex"
```

## Running the Tests

```bash
source venv/bin/activate
pytest tests/ -v
```

There are 78 tests total covering all the models and CLI commands. Writing tests was actually really useful - I caught a bug where duplicate task checking was case-sensitive when it shouldn't have been.

## Design Decisions

I used OOP concepts we covered in class:
- **Person** is the base class (just name + email)
- **User** inherits from Person and owns a list of projects
- **Project** holds tasks and calculates a completion percentage
- **Task** has three statuses: `pending`, `in_progress`, and `complete`

I also used a registry pattern for the User class (a class-level dictionary that keeps track of all users) which I found online. It acts like a simple in-memory database without needing SQLite or anything like that.

## How Saving Works

Everything gets stored in `data/users.json`. The file is created automatically the first time you add a user - you don't need to create it yourself. The structure is nested: users → projects → tasks. When you run any command it loads the whole file, makes the change, and saves it back.

I know rewriting the entire file every time isn't the most efficient approach but for a CLI tool used by one person it's totally fine.
