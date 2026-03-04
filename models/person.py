"""
person.py - Base Person class

This is the parent class that User inherits from.
We learned about inheritance this semester and I wanted to actually
use it in a real project. Person felt like the right base class since
a user is basically just a person with extra stuff added on.

I also used @property decorators here which we covered in week 6.
They're a bit weird at first but I like how they let you validate
values before setting them.
"""


class Person:
    """Base class representing a person - just name and email for now"""

    def __init__(self, name: str, email: str = ""):
        """
        Create a new person.
        Email is optional because not everyone wants to give their email.
        The .strip() calls remove any accidental spaces the user might type.
        """
        self._name = name.strip()
        self._email = email.strip()

    # using @property so I can add validation without changing how the code looks
    # from the outside. Learned about this pattern in week 6.

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        # don't allow blank names - that would break a lot of things downstream
        if not value or not value.strip():
            raise ValueError("Name cannot be empty.")
        self._name = value.strip()

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        # email doesn't need validation here - that's handled in validators.py
        self._email = value.strip()

    # these two methods make it easier to print Person objects for debugging

    def __repr__(self) -> str:
        # repr is for developers (shows in the debugger etc.)
        return f"{self.__class__.__name__}(name={self._name!r}, email={self._email!r})"

    def __str__(self) -> str:
        # str is for end users (shows when you print() the object)
        return f"{self._name} <{self._email}>" if self._email else self._name

    def to_dict(self) -> dict:
        """Convert this person to a plain dictionary so it can be saved to JSON"""
        return {"name": self._name, "email": self._email}
