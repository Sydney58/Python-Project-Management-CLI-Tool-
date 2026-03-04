"""
models/__init__.py

Makes the models folder a package and exposes the main classes.
So you can do `from models import User` instead of `from models.user import User`.
"""
from .user import User
from .project import Project
from .task import Task

__all__ = ["User", "Project", "Task"]
