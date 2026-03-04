"""
user.py - User class (extends Person)

Users can own multiple projects. To keep track of all users without
needing a real database, I'm using a class-level dictionary called _registry.
It maps lowercase names to User objects, kind of like a simple in-memory database.

I found the registry pattern on Stack Overflow and thought it was really clever.
Basically the class itself keeps track of all its instances.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

from .person import Person
from .project import Project


class User(Person):
    """User class - inherits from Person and can have multiple projects"""

    # This is a class variable (shared across all instances, not per-instance)
    # Keys are lowercase names, values are User objects
    # e.g. {"alice": <User alice>, "bob": <User bob>}
    _registry: dict[str, "User"] = {}

    def __init__(
        self,
        name: str,
        email: str = "",
        user_id: str | None = None,
    ) -> None:
        """
        Create a new user.
        Calls super().__init__() to run Person's __init__ first (inheritance!).
        user_id is only passed when loading from saved data.
        """
        super().__init__(name=name, email=email)
        self._id: str = user_id or str(uuid.uuid4())
        self._projects: List[Project] = []

    # --- properties ---

    @property
    def id(self) -> str:
        return self._id

    @property
    def projects(self) -> List[Project]:
        # return a copy of the list - same reason as in Project.tasks
        return list(self._projects)

    # --- project management ---

    def add_project(self, project: Project) -> None:
        """Add a project to this user. Raises ValueError if title already exists."""
        # check for duplicates - two projects with the same name would be confusing
        for existing in self._projects:
            if existing.title.lower() == project.title.lower():
                raise ValueError(
                    f"Project '{project.title}' already exists for user '{self._name}'."
                )
        self._projects.append(project)

    def get_project(self, title: str) -> Optional[Project]:
        """Find a project by title (case-insensitive). Returns None if not found."""
        for project in self._projects:
            if project.title.lower() == title.lower():
                return project
        return None

    def remove_project(self, title: str) -> bool:
        """Remove a project by title. Returns True if removed, False if not found."""
        for i, project in enumerate(self._projects):
            if project.title.lower() == title.lower():
                self._projects.pop(i)
                return True
        return False

    # --- class-level registry methods ---
    # these are classmethods because they work on the registry (class variable)
    # rather than on a specific user instance

    @classmethod
    def register(cls, user: "User") -> None:
        """Add a user to the registry so they can be looked up later"""
        cls._registry[user.name.lower()] = user

    @classmethod
    def find(cls, name: str) -> Optional["User"]:
        """Look up a user by name. Case-insensitive. Returns None if not found."""
        return cls._registry.get(name.lower())

    @classmethod
    def all_users(cls) -> List["User"]:
        """Return a list of all registered users"""
        return list(cls._registry.values())

    @classmethod
    def clear_registry(cls) -> None:
        """
        Remove all users from the registry.
        Mostly used in tests to start fresh between test cases.
        """
        cls._registry.clear()

    # --- JSON serialization ---

    def to_dict(self) -> dict:
        """Serialize user to a dictionary. Calls super().to_dict() to get name/email first."""
        base = super().to_dict()  # gets {"name": ..., "email": ...} from Person
        base["id"] = self._id
        base["projects"] = [p.to_dict() for p in self._projects]
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Rebuild a User from a saved dictionary (used by Storage.load())"""
        user = cls(
            name=data["name"],
            email=data.get("email", ""),
            user_id=data.get("id"),
        )
        # rebuild each project (and their tasks) too
        for project_data in data.get("projects", []):
            user._projects.append(Project.from_dict(project_data))
        return user

    # --- string representations ---

    def __str__(self) -> str:
        email_part = f" <{self._email}>" if self._email else ""
        return f"{self._name}{email_part} — {len(self._projects)} project(s)"

    def __repr__(self) -> str:
        return f"User(name={self._name!r}, email={self._email!r})"
