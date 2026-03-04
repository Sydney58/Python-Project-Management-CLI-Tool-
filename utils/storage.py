"""
utils/storage.py - Saving and loading data to/from a JSON file

All data lives in data/users.json. I picked JSON because:
  1. It's easy to read as a human (helpful for debugging)
  2. Python's built-in json module handles it with no extra libraries
  3. We used JSON in class so I already know how it works

The file gets created automatically the first time you save.
If the file is corrupted/missing we just start fresh instead of crashing.
"""
from __future__ import annotations

import json
import logging
import os
from typing import List

from models.user import User

logger = logging.getLogger(__name__)

# build the path to data/users.json relative to this file's location
# __file__ is the path to storage.py, dirname twice gets us to the project root
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")


class Storage:
    """Handles loading and saving all app data to disk"""

    @staticmethod
    def _ensure_data_dir() -> None:
        """Create the data/ directory if it doesn't exist yet"""
        os.makedirs(DATA_DIR, exist_ok=True)  # exist_ok means no error if already there

    @classmethod
    def load(cls) -> List[User]:
        """
        Load all users (and their projects/tasks) from the JSON file.
        Clears the registry first so we don't end up with duplicate users.
        Returns the list of loaded users (though most callers don't use it).
        """
        cls._ensure_data_dir()
        User.clear_registry()  # start fresh before loading

        # if the file doesn't exist yet, that's fine - just means no data saved yet
        if not os.path.exists(USERS_FILE):
            logger.debug("No data file found at %s. Starting fresh.", USERS_FILE)
            return []

        try:
            with open(USERS_FILE, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except json.JSONDecodeError as exc:
            # file is corrupted somehow - log it and start fresh
            logger.error("Malformed JSON in %s: %s", USERS_FILE, exc)
            return []
        except OSError as exc:
            # couldn't read the file for some OS reason
            logger.error("Could not read %s: %s", USERS_FILE, exc)
            return []

        users: List[User] = []
        for user_data in raw.get("users", []):
            try:
                user = User.from_dict(user_data)
                User.register(user)
                users.append(user)
            except (KeyError, ValueError) as exc:
                # skip any records that are malformed instead of crashing everything
                logger.warning("Skipping malformed user record: %s", exc)

        logger.debug("Loaded %d user(s) from %s.", len(users), USERS_FILE)
        return users

    @classmethod
    def save(cls) -> None:
        """
        Save all current users (and their projects/tasks) to the JSON file.
        Overwrites the whole file each time - not super efficient but simple and safe.
        """
        cls._ensure_data_dir()
        payload = {"users": [u.to_dict() for u in User.all_users()]}

        try:
            with open(USERS_FILE, "w", encoding="utf-8") as fh:
                # indent=2 makes the JSON file human-readable
                # ensure_ascii=False allows non-English characters
                json.dump(payload, fh, indent=2, ensure_ascii=False)
            logger.debug("Saved %d user(s) to %s.", len(payload["users"]), USERS_FILE)
        except OSError as exc:
            logger.error("Could not write to %s: %s", USERS_FILE, exc)
            raise  # re-raise so the caller knows something went wrong
