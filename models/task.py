"""
task.py - Task class

Tasks are the smallest unit in the whole system.
Each task belongs to a project and can be in one of three states:
  - pending    (just created, nothing started)
  - in_progress (someone is working on it)
  - complete   (done!)

I thought about using an Enum for the statuses but a set of strings
felt simpler and easier to work with for JSON serialization.
Maybe I'd use an Enum in a v2.
"""
from __future__ import annotations

import uuid  # for generating unique IDs - learned about this in week 10


class Task:
    """Represents a single task inside a project"""

    # class variable holding all the allowed status values
    # using a set because checking `x in set` is O(1) which is faster than a list
    # (probably doesn't matter at this scale but good habit I guess)
    VALID_STATUSES = {"pending", "in_progress", "complete"}

    def __init__(
        self,
        title: str,
        assigned_to: str = "",
        status: str = "pending",
        task_id: str | None = None,
    ) -> None:
        """
        Create a new task.
        - title: what the task is (required)
        - assigned_to: who's doing it (optional)
        - status: starts as pending by default
        - task_id: only pass this when loading from saved JSON, otherwise
                   we generate a fresh UUID automatically
        """
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty.")
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Choose from {self.VALID_STATUSES}.")

        # uuid4 gives a random unique ID - no two tasks will ever have the same one
        self._id: str = task_id or str(uuid.uuid4())
        self._title: str = title.strip()
        self._status: str = status
        self._assigned_to: str = assigned_to.strip()

    # properties for all the private attributes

    @property
    def id(self) -> str:
        return self._id

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Task title cannot be empty.")
        self._title = value.strip()

    @property
    def status(self) -> str:
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        # always validate before setting - don't want garbage data in the system
        if value not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status '{value}'. Choose from {self.VALID_STATUSES}.")
        self._status = value

    @property
    def assigned_to(self) -> str:
        return self._assigned_to

    @assigned_to.setter
    def assigned_to(self, value: str) -> None:
        self._assigned_to = value.strip()

    # convenience methods so you don't have to remember the exact status strings

    def mark_complete(self) -> None:
        """Mark this task as done"""
        self._status = "complete"

    def mark_in_progress(self) -> None:
        """Mark this task as in progress (someone started working on it)"""
        self._status = "in_progress"

    # JSON serialization - needed for saving to the data file

    def to_dict(self) -> dict:
        """Turn this task into a plain dict that can be written to JSON"""
        return {
            "id": self._id,
            "title": self._title,
            "status": self._status,
            "assigned_to": self._assigned_to,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """
        Rebuild a Task object from a dictionary (used when loading from JSON).
        The classmethod decorator means we call this on the class itself,
        not on an instance - like Task.from_dict(data) instead of task.from_dict(data)
        """
        return cls(
            title=data["title"],
            assigned_to=data.get("assigned_to", ""),
            status=data.get("status", "pending"),
            task_id=data.get("id"),
        )

    # string representations

    def __str__(self) -> str:
        assignee = f" → {self._assigned_to}" if self._assigned_to else ""
        return f"[{self._status.upper()}] {self._title}{assignee}"

    def __repr__(self) -> str:
        return (
            f"Task(title={self._title!r}, status={self._status!r}, "
            f"assigned_to={self._assigned_to!r})"
        )
