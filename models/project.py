"""
project.py - Project class

Projects belong to a user and contain tasks.
The completion_rate property was the most math-y part of this whole project -
it just divides completed tasks by total tasks and multiplies by 100.
Basic stuff but I'm glad it works correctly.

I also added a find_by_title class method because I kept writing the same
"loop through projects looking for a title match" code everywhere.
DRY principle!
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from .task import Task


class Project:
    """A project - has a title, owner, optional description/due date, and a list of tasks"""

    def __init__(
        self,
        title: str,
        owner: str,
        description: str = "",
        due_date: str = "",
        project_id: str | None = None,
    ) -> None:
        """
        Create a new project.
        project_id should only be passed when loading from saved data -
        we generate a new UUID automatically for brand new projects.
        """
        if not title or not title.strip():
            raise ValueError("Project title cannot be empty.")
        if not owner or not owner.strip():
            raise ValueError("Project must have an owner.")

        self._id: str = project_id or str(uuid.uuid4())
        self._title: str = title.strip()
        self._owner: str = owner.strip()
        self._description: str = description.strip()
        self._due_date: str = due_date.strip()
        self._tasks: List[Task] = []  # starts empty, tasks get added later

    # --- properties ---

    @property
    def id(self) -> str:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Project title cannot be empty.")
        self._title = value.strip()

    @property
    def owner(self) -> str:
        return self._owner

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = value.strip()

    @property
    def due_date(self) -> str:
        return self._due_date

    @due_date.setter
    def due_date(self, value: str) -> None:
        self._due_date = value.strip()

    @property
    def tasks(self) -> List[Task]:
        # return a copy of the list so outside code can't accidentally modify it
        # e.g. someone doing project.tasks.append(task) would not work
        # they have to use add_task() instead
        return list(self._tasks)

    # --- task management ---

    def add_task(self, task: Task) -> None:
        """Add a task to this project. Raises ValueError if the title is already taken."""
        # check for duplicate task titles (case-insensitive)
        for existing in self._tasks:
            if existing.title.lower() == task.title.lower():
                raise ValueError(f"Task '{task.title}' already exists in project '{self._title}'.")
        self._tasks.append(task)

    def get_task(self, title: str) -> Optional[Task]:
        """Find and return a task by title, or None if it doesn't exist"""
        for task in self._tasks:
            if task.title.lower() == title.lower():
                return task
        return None

    def remove_task(self, title: str) -> bool:
        """
        Remove a task by title.
        Returns True if it was found and removed, False if it wasn't there.
        I like this pattern better than raising an exception - lets the caller decide.
        """
        for i, task in enumerate(self._tasks):
            if task.title.lower() == title.lower():
                self._tasks.pop(i)
                return True
        return False

    @property
    def completion_rate(self) -> float:
        """
        Calculate what percentage of tasks are complete.
        Returns 0.0 if there are no tasks (avoid division by zero).
        """
        if not self._tasks:
            return 0.0
        # count how many tasks have status == "complete"
        completed = sum(1 for t in self._tasks if t.status == "complete")
        return round(completed / len(self._tasks) * 100, 1)

    # --- class methods ---

    @classmethod
    def find_by_title(cls, projects: List["Project"], title: str) -> Optional["Project"]:
        """
        Search a list of projects for one with a matching title.
        Case-insensitive, returns None if not found.
        """
        for project in projects:
            if project.title.lower() == title.lower():
                return project
        return None

    # --- JSON serialization ---

    def to_dict(self) -> dict:
        """Serialize this project to a plain dictionary for JSON storage"""
        return {
            "id": self._id,
            "title": self._title,
            "owner": self._owner,
            "description": self._description,
            "due_date": self._due_date,
            "tasks": [t.to_dict() for t in self._tasks],  # serialize each task too
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Project":
        """
        Rebuild a Project from a saved dictionary.
        Uses .get() with defaults for optional fields in case old data doesn't have them.
        """
        project = cls(
            title=data["title"],
            owner=data["owner"],
            description=data.get("description", ""),
            due_date=data.get("due_date", ""),
            project_id=data.get("id"),
        )
        # rebuild each task too
        for task_data in data.get("tasks", []):
            project._tasks.append(Task.from_dict(task_data))
        return project

    # --- string representations ---

    def __str__(self) -> str:
        due = f" (due: {self._due_date})" if self._due_date else ""
        return f"Project: {self._title}{due} | Owner: {self._owner} | Tasks: {len(self._tasks)}"

    def __repr__(self) -> str:
        return f"Project(title={self._title!r}, owner={self._owner!r})"
