"""
main.py - the main file for my project management CLI

This is where all the command-line argument stuff happens.
I used argparse for this which we learned about in week 8 of the course.
It was really confusing at first but I think I finally understand subparsers now.

Took me way too long to figure out why my commands weren't showing up - turns out
I forgot to call set_defaults(func=...) on each subparser. Ugh.

"""
from __future__ import annotations

import argparse
import logging
import sys

from models.user import User
from models.project import Project
from models.task import Task
from utils.storage import Storage
from utils.display import Display
from utils.validators import validate_date, validate_email

# set up logging - I mostly use this when something breaks and I need to debug
# WARNING level means it only shows actual problems, not all the debug spam
logging.basicConfig(
    level=logging.WARNING,
    format="[%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cli")


# -----------------------------------------------------------------------
# Command handler functions
# Each function below handles exactly one CLI command
# I named them cmd_* so I can find them easily
# -----------------------------------------------------------------------


def cmd_add_user(args: argparse.Namespace) -> int:
    """Handles the add-user command"""
    # first validate the email before doing anything else
    try:
        email = validate_email(args.email or "")
    except ValueError as exc:
        Display.error(str(exc))
        return 1

    # make sure we're not creating a duplicate user
    if User.find(args.name):
        Display.error(f"User '{args.name}' already exists.")
        return 1

    user = User(name=args.name, email=email)
    User.register(user)
    Storage.save()
    Display.success(f"User '{user.name}' created successfully.")
    return 0


def cmd_list_users(_args: argparse.Namespace) -> int:
    """Shows all users. The underscore prefix means I'm not using the args parameter"""
    Display.list_users(User.all_users())
    return 0


def cmd_delete_user(args: argparse.Namespace) -> int:
    """Delete a user and everything that belongs to them (projects, tasks, etc.)"""
    user = User.find(args.name)
    if not user:
        Display.error(f"User '{args.name}' not found.")
        return 1

    # remove from the registry dict directly
    # user.name.lower() because the registry stores everything lowercase
    User._registry.pop(user.name.lower())
    Storage.save()
    Display.success(f"User '{user.name}' deleted.")
    return 0


# --- project commands ---


def cmd_add_project(args: argparse.Namespace) -> int:
    """Add a new project under a user"""
    user = User.find(args.user)
    if not user:
        Display.error(f"User '{args.user}' not found. Create them first with 'add-user'.")
        return 1

    # validate the due date if one was given
    try:
        due = validate_date(args.due_date or "")
    except ValueError as exc:
        Display.error(str(exc))
        return 1

    try:
        project = Project(
            title=args.title,
            owner=user.name,
            description=args.description or "",
            due_date=due,
        )
        user.add_project(project)
    except ValueError as exc:
        Display.error(str(exc))
        return 1

    Storage.save()
    Display.success(f"Project '{project.title}' added to user '{user.name}'.")
    return 0


def cmd_list_projects(args: argparse.Namespace) -> int:
    """List all projects, or just the ones for a specific user"""
    if args.user:
        user = User.find(args.user)
        if not user:
            Display.error(f"User '{args.user}' not found.")
            return 1
        Display.list_projects(user.projects, owner=user.name)
    else:
        # I used a list comprehension here - proud of this one lol
        # basically: for every user, get all their projects and flatten into one list
        all_projects = [p for u in User.all_users() for p in u.projects]
        Display.list_projects(all_projects)
    return 0


def cmd_view_project(args: argparse.Namespace) -> int:
    """Show detailed info for a specific project"""
    project = _find_project(args.title, args.user if hasattr(args, "user") else None)
    if not project:
        Display.error(f"Project '{args.title}' not found.")
        return 1
    Display.project_detail(project)
    return 0


def cmd_delete_project(args: argparse.Namespace) -> int:
    """Delete a project from a user"""
    user = User.find(args.user)
    if not user:
        Display.error(f"User '{args.user}' not found.")
        return 1

    if not user.remove_project(args.title):
        Display.error(f"Project '{args.title}' not found for user '{args.user}'.")
        return 1

    Storage.save()
    Display.success(f"Project '{args.title}' deleted from user '{args.user}'.")
    return 0


def cmd_update_project(args: argparse.Namespace) -> int:
    """Update a project's description or due date (or both)"""
    user = User.find(args.user)
    if not user:
        Display.error(f"User '{args.user}' not found.")
        return 1

    project = user.get_project(args.title)
    if not project:
        Display.error(f"Project '{args.title}' not found for user '{args.user}'.")
        return 1

    # only update the fields that were actually passed in
    if args.description:
        project.description = args.description
    if args.due_date:
        try:
            project.due_date = validate_date(args.due_date)
        except ValueError as exc:
            Display.error(str(exc))
            return 1

    Storage.save()
    Display.success(f"Project '{project.title}' updated.")
    return 0


# --- task commands ---


def cmd_add_task(args: argparse.Namespace) -> int:
    """Add a task to an existing project"""
    project = _find_project(args.project, args.user if hasattr(args, "user") else None)
    if not project:
        Display.error(f"Project '{args.project}' not found.")
        return 1

    try:
        task = Task(title=args.title, assigned_to=args.assigned_to or "")
        project.add_task(task)
    except ValueError as exc:
        Display.error(str(exc))
        return 1

    Storage.save()
    Display.success(f"Task '{task.title}' added to project '{project.title}'.")
    return 0


def cmd_list_tasks(args: argparse.Namespace) -> int:
    """List all the tasks in a project"""
    project = _find_project(args.project, args.user if hasattr(args, "user") else None)
    if not project:
        Display.error(f"Project '{args.project}' not found.")
        return 1
    Display.list_tasks(project.tasks, project.title)
    return 0


def cmd_complete_task(args: argparse.Namespace) -> int:
    """Mark a task as complete"""
    return _set_task_status(args, "complete")


def cmd_start_task(args: argparse.Namespace) -> int:
    """Mark a task as in progress"""
    return _set_task_status(args, "in_progress")


def cmd_delete_task(args: argparse.Namespace) -> int:
    """Delete a task from a project"""
    project = _find_project(args.project, args.user if hasattr(args, "user") else None)
    if not project:
        Display.error(f"Project '{args.project}' not found.")
        return 1

    if not project.remove_task(args.task):
        Display.error(f"Task '{args.task}' not found in project '{args.project}'.")
        return 1

    Storage.save()
    Display.success(f"Task '{args.task}' deleted from project '{args.project}'.")
    return 0


# -----------------------------------------------------------------------
# Helper / utility functions
# I pulled these out of the command handlers because they were being
# repeated over and over - DRY principle (Don't Repeat Yourself)!
# -----------------------------------------------------------------------


def _find_project(title: str, user_name: str | None = None) -> Project | None:
    """
    Look up a project by title.
    If user_name is given, only search that user's projects.
    If no user_name, search all users (slower but more convenient).
    Returns None if we can't find it.
    """
    if user_name:
        user = User.find(user_name)
        return user.get_project(title) if user else None

    # search through every user's projects - not the most efficient but works fine
    for user in User.all_users():
        project = user.get_project(title)
        if project:
            return project
    return None


def _set_task_status(args: argparse.Namespace, status: str) -> int:
    """
    Helper to change a task's status.
    I made this a separate function because start-task and complete-task
    were basically doing the exact same thing - just with a different status string.
    """
    project = _find_project(args.project, args.user if hasattr(args, "user") else None)
    if not project:
        Display.error(f"Project '{args.project}' not found.")
        return 1

    task = project.get_task(args.task)
    if not task:
        Display.error(f"Task '{args.task}' not found in project '{args.project}'.")
        return 1

    task.status = status
    Storage.save()
    Display.success(f"Task '{task.title}' marked as '{status}'.")
    return 0


# -----------------------------------------------------------------------
# Argument parser setup
# This was honestly the trickiest part of the whole project.
# Argparse docs are... not great. I spent like 3 hours on this section.
# The key insight is that each subcommand gets its own sub-parser.
# -----------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser with all subcommands configured"""
    parser = argparse.ArgumentParser(
        prog="project-mgr",
        description="📋  Python Project Management CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # this shows up at the bottom of --help, nice touch I think
        epilog=(
            "Examples:\n"
            "  python main.py add-user --name Alex --email alex@example.com\n"
            "  python main.py add-project --user Alex --title 'CLI Tool'\n"
            "  python main.py add-task --project 'CLI Tool' --title 'Write tests'\n"
            "  python main.py complete-task --project 'CLI Tool' --task 'Write tests'\n"
            "  python main.py list-projects --user Alex\n"
        ),
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging output."
    )

    # sub is the object that holds all our subcommands
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True  # show error if no command given instead of doing nothing

    # --- user commands ---
    p_add_user = sub.add_parser("add-user", help="Create a new user.")
    p_add_user.add_argument("--name", required=True, help="User's full name.")
    p_add_user.add_argument("--email", default="", help="User's email address (optional).")
    p_add_user.set_defaults(func=cmd_add_user)

    p_list_users = sub.add_parser("list-users", help="List all users.")
    p_list_users.set_defaults(func=cmd_list_users)

    p_del_user = sub.add_parser("delete-user", help="Delete a user and their data.")
    p_del_user.add_argument("--name", required=True, help="Name of the user to delete.")
    p_del_user.set_defaults(func=cmd_delete_user)

    # --- project commands ---
    p_add_proj = sub.add_parser("add-project", help="Add a project to a user.")
    p_add_proj.add_argument("--user", required=True, help="Owner's name.")
    p_add_proj.add_argument("--title", required=True, help="Project title.")
    p_add_proj.add_argument("--description", default="", help="Short description.")
    p_add_proj.add_argument("--due-date", default="", dest="due_date", help="Due date (YYYY-MM-DD or natural language).")
    p_add_proj.set_defaults(func=cmd_add_project)

    p_list_proj = sub.add_parser("list-projects", help="List projects (all or per user).")
    p_list_proj.add_argument("--user", default="", help="Filter by user name.")
    p_list_proj.set_defaults(func=cmd_list_projects)

    p_view_proj = sub.add_parser("view-project", help="View detailed info on a project.")
    p_view_proj.add_argument("--title", required=True, help="Project title.")
    p_view_proj.add_argument("--user", default="", help="Owner's name (helps if two projects have same name).")
    p_view_proj.set_defaults(func=cmd_view_project)

    p_upd_proj = sub.add_parser("update-project", help="Update project description or due date.")
    p_upd_proj.add_argument("--user", required=True, help="Owner's name.")
    p_upd_proj.add_argument("--title", required=True, help="Project title.")
    p_upd_proj.add_argument("--description", default="", help="New description.")
    p_upd_proj.add_argument("--due-date", default="", dest="due_date", help="New due date.")
    p_upd_proj.set_defaults(func=cmd_update_project)

    p_del_proj = sub.add_parser("delete-project", help="Delete a project from a user.")
    p_del_proj.add_argument("--user", required=True, help="Owner's name.")
    p_del_proj.add_argument("--title", required=True, help="Project title.")
    p_del_proj.set_defaults(func=cmd_delete_project)

    # --- task commands ---
    p_add_task = sub.add_parser("add-task", help="Add a task to a project.")
    p_add_task.add_argument("--project", required=True, help="Project title.")
    p_add_task.add_argument("--title", required=True, help="Task title.")
    p_add_task.add_argument("--assigned-to", default="", dest="assigned_to", help="Who is doing this task.")
    p_add_task.add_argument("--user", default="", help="Project owner (needed if project name isn't unique).")
    p_add_task.set_defaults(func=cmd_add_task)

    p_list_tasks = sub.add_parser("list-tasks", help="List tasks for a project.")
    p_list_tasks.add_argument("--project", required=True, help="Project title.")
    p_list_tasks.add_argument("--user", default="", help="Project owner.")
    p_list_tasks.set_defaults(func=cmd_list_tasks)

    p_complete = sub.add_parser("complete-task", help="Mark a task as complete.")
    p_complete.add_argument("--project", required=True, help="Project title.")
    p_complete.add_argument("--task", required=True, help="Task title.")
    p_complete.add_argument("--user", default="", help="Project owner.")
    p_complete.set_defaults(func=cmd_complete_task)

    p_start = sub.add_parser("start-task", help="Mark a task as in progress.")
    p_start.add_argument("--project", required=True, help="Project title.")
    p_start.add_argument("--task", required=True, help="Task title.")
    p_start.add_argument("--user", default="", help="Project owner.")
    p_start.set_defaults(func=cmd_start_task)

    p_del_task = sub.add_parser("delete-task", help="Delete a task from a project.")
    p_del_task.add_argument("--project", required=True, help="Project title.")
    p_del_task.add_argument("--task", required=True, help="Task title.")
    p_del_task.add_argument("--user", default="", help="Project owner.")
    p_del_task.set_defaults(func=cmd_delete_task)

    return parser


# -----------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """
    Main entry point. Parses args, loads saved data, runs the right command.
    The argv parameter lets me pass in fake arguments during testing
    instead of having to mess with sys.argv directly.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # turn on debug logging if --debug flag was passed
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled.")

    # load all the saved users/projects/tasks from the JSON file
    Storage.load()

    # args.func is whichever cmd_* function was set by set_defaults()
    # this is the argparse dispatch pattern - pretty neat once you get it
    exit_code: int = args.func(args)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
