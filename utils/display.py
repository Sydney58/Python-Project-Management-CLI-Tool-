"""
utils/display.py - All the terminal output stuff

I discovered the `rich` library while looking for ways to make the CLI
look better and honestly it's amazing. You can make really nice tables
and colored output without too much code.

I spent way too long tweaking colors and table styles lol.
But I think it looks really professional now.

References:
  https://rich.readthedocs.io/en/stable/tables.html
  https://rich.readthedocs.io/en/stable/panel.html
"""
from __future__ import annotations

from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

from models.user import User
from models.project import Project
from models.task import Task

# one global Console object - rich uses this to print everything
console = Console()

# maps task status strings to terminal colors
# makes it easy to see at a glance what state each task is in
STATUS_COLORS = {
    "pending": "yellow",
    "in_progress": "blue",
    "complete": "green",
}


class Display:
    """
    All the display/print methods for the CLI.
    I made them all static methods because they don't need any instance state -
    they just take data and print it.
    """

    # --- basic message helpers ---

    @staticmethod
    def success(message: str) -> None:
        """Print a green success message with a checkmark"""
        console.print(f"[bold green]✔ {message}[/bold green]")

    @staticmethod
    def error(message: str) -> None:
        """Print a red error message with an X"""
        console.print(f"[bold red]✘ {message}[/bold red]")

    @staticmethod
    def info(message: str) -> None:
        """Print a cyan informational message"""
        console.print(f"[cyan]{message}[/cyan]")

    @staticmethod
    def warn(message: str) -> None:
        """Print a yellow warning message"""
        console.print(f"[yellow]⚠ {message}[/yellow]")

    # --- user display ---

    @staticmethod
    def list_users(users: List[User]) -> None:
        """Display all users in a nicely formatted table"""
        if not users:
            Display.info("No users found. Use 'add-user' to create one.")
            return

        table = Table(
            title="Registered Users",
            box=box.ROUNDED,
            header_style="bold magenta",
            show_lines=True,
        )
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Name", style="bold white")
        table.add_column("Email", style="cyan")
        table.add_column("Projects", justify="center")

        for idx, user in enumerate(users, start=1):
            table.add_row(
                str(idx),
                user.name,
                user.email or "—",  # show a dash if no email
                str(len(user.projects)),
            )

        console.print(table)

    # --- project display ---

    @staticmethod
    def list_projects(projects: List[Project], owner: str = "") -> None:
        """Display a list of projects as a table. Shows completion % with color coding."""
        if not projects:
            Display.info("No projects found.")
            return

        # title changes based on whether we're filtering by owner or showing all
        title = f"Projects for {owner}" if owner else "All Projects"
        table = Table(
            title=title,
            box=box.ROUNDED,
            header_style="bold blue",
            show_lines=True,
        )
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Title", style="bold white")
        table.add_column("Description")
        table.add_column("Due Date", style="cyan")
        table.add_column("Tasks", justify="center")
        table.add_column("Done %", justify="right")

        for idx, project in enumerate(projects, start=1):
            completion = project.completion_rate
            # green = done, yellow = in progress, white = not started
            color = "green" if completion == 100 else "yellow" if completion > 0 else "white"
            table.add_row(
                str(idx),
                project.title,
                project.description or "—",
                project.due_date or "—",
                str(len(project.tasks)),
                f"[{color}]{completion}%[/{color}]",
            )

        console.print(table)

    # --- task display ---

    @staticmethod
    def list_tasks(tasks: List[Task], project_title: str = "") -> None:
        """Display tasks for a project. Status is color-coded using STATUS_COLORS."""
        if not tasks:
            Display.info("No tasks found for this project.")
            return

        title = f"Tasks — {project_title}" if project_title else "Tasks"
        table = Table(
            title=title,
            box=box.ROUNDED,
            header_style="bold cyan",
            show_lines=True,
        )
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Title", style="bold white")
        table.add_column("Status", justify="center")
        table.add_column("Assigned To")

        for idx, task in enumerate(tasks, start=1):
            color = STATUS_COLORS.get(task.status, "white")
            # replace underscores and capitalize for nicer display
            # e.g. "in_progress" -> "In Progress"
            status_text = Text(task.status.replace("_", " ").title(), style=f"bold {color}")
            table.add_row(
                str(idx),
                task.title,
                status_text,
                task.assigned_to or "—",
            )

        console.print(table)

    # --- detailed project view ---

    @staticmethod
    def project_detail(project: Project) -> None:
        """
        Show all details for one project in a rich Panel, then list its tasks below.
        Panels are like a bordered box - looks really clean in the terminal.
        """
        lines: List[str] = [
            f"[bold]Owner:[/bold]       {project.owner}",
            f"[bold]Description:[/bold] {project.description or '—'}",
            f"[bold]Due Date:[/bold]    {project.due_date or '—'}",
            f"[bold]Completion:[/bold]  {project.completion_rate}%",
        ]
        panel_content = "\n".join(lines)
        console.print(
            Panel(panel_content, title=f"[bold blue]{project.title}[/bold blue]", expand=False)
        )
        # show the tasks below the panel
        Display.list_tasks(project.tasks, project.title)
