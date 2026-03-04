"""
test_cli.py - Tests for the CLI command handlers in main.py

Testing CLI commands was tricky because they normally read/write files
and use the global User registry. I had to figure out how to isolate each test.

The solution was monkeypatching (replacing Storage.save/load with no-ops)
and clearing the User registry before each test. Took a while to figure out
but it works really well now.

Run all tests: pytest tests/ -v
"""
import pytest
from models.user import User
from models.project import Project
from models.task import Task
import main as cli_module


# -----------------------------------------------------------------------
# Shared fixtures
# -----------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_registry(monkeypatch):
    """
    This fixture runs before every single test automatically (autouse=True).
    It clears the User registry and replaces Storage methods with no-ops
    so tests don't actually touch the filesystem.
    """
    User.clear_registry()
    monkeypatch.setattr("main.Storage.save", lambda: None)
    monkeypatch.setattr("main.Storage.load", lambda: [])
    yield
    User.clear_registry()  # clean up after each test too


def _run(argv: list) -> int:
    """Helper to call main() with a list of arguments. Returns the exit code."""
    return cli_module.main(argv)


# -----------------------------------------------------------------------
# add-user tests
# -----------------------------------------------------------------------

class TestAddUser:
    def test_success(self):
        assert _run(["add-user", "--name", "Alice", "--email", "a@b.com"]) == 0
        assert User.find("alice") is not None

    def test_no_email(self):
        # email is optional - should work fine without it
        assert _run(["add-user", "--name", "Bob"]) == 0
        assert User.find("bob").email == ""

    def test_duplicate_fails(self):
        _run(["add-user", "--name", "Carol"])
        assert _run(["add-user", "--name", "Carol"]) == 1  # second one should fail

    def test_bad_email_fails(self):
        assert _run(["add-user", "--name", "Dave", "--email", "bad"]) == 1


# -----------------------------------------------------------------------
# list-users and delete-user tests
# -----------------------------------------------------------------------

class TestUserCommands:
    def test_list_empty(self):
        # should succeed even with no users
        assert _run(["list-users"]) == 0

    def test_list_with_users(self):
        User.register(User(name="Zara"))
        assert _run(["list-users"]) == 0

    def test_delete_existing(self):
        User.register(User(name="Temp"))
        assert _run(["delete-user", "--name", "Temp"]) == 0
        assert User.find("temp") is None

    def test_delete_missing_fails(self):
        assert _run(["delete-user", "--name", "Ghost"]) == 1


# -----------------------------------------------------------------------
# project command tests
# -----------------------------------------------------------------------

class TestProjectCommands:
    def _user(self, name="Alice"):
        """Helper to register a user and return them"""
        u = User(name=name)
        User.register(u)
        return u

    def test_add_project_success(self):
        self._user("Alice")
        assert _run(["add-project", "--user", "Alice", "--title", "P1"]) == 0
        assert User.find("alice").get_project("P1") is not None

    def test_add_project_unknown_user_fails(self):
        assert _run(["add-project", "--user", "Nobody", "--title", "X"]) == 1

    def test_add_project_with_due_date(self):
        self._user("Beth")
        _run(["add-project", "--user", "Beth", "--title", "D", "--due-date", "2025-06-30"])
        assert User.find("beth").get_project("D").due_date == "2025-06-30"

    def test_add_duplicate_project_fails(self):
        self._user("Carol")
        _run(["add-project", "--user", "Carol", "--title", "Dup"])
        assert _run(["add-project", "--user", "Carol", "--title", "Dup"]) == 1

    def test_list_projects_for_user(self):
        u = self._user("Dan")
        u.add_project(Project(title="P", owner="Dan"))
        assert _run(["list-projects", "--user", "Dan"]) == 0

    def test_list_projects_unknown_user_fails(self):
        assert _run(["list-projects", "--user", "Ghost"]) == 1

    def test_list_all_projects(self):
        assert _run(["list-projects"]) == 0

    def test_view_project_success(self):
        u = self._user("Hank")
        u.add_project(Project(title="ViewMe", owner="Hank"))
        assert _run(["view-project", "--title", "ViewMe", "--user", "Hank"]) == 0

    def test_view_project_missing_fails(self):
        assert _run(["view-project", "--title", "NoProj"]) == 1

    def test_update_description(self):
        u = self._user("Ivy")
        p = Project(title="Upd", owner="Ivy")
        u.add_project(p)
        _run(["update-project", "--user", "Ivy", "--title", "Upd", "--description", "New"])
        assert p.description == "New"

    def test_update_unknown_user_fails(self):
        assert _run(["update-project", "--user", "Ghost", "--title", "X", "--description", "Y"]) == 1

    def test_delete_project_success(self):
        u = self._user("Jake")
        u.add_project(Project(title="Del", owner="Jake"))
        assert _run(["delete-project", "--user", "Jake", "--title", "Del"]) == 0
        assert User.find("jake").get_project("Del") is None

    def test_delete_project_missing_fails(self):
        self._user("Ken")
        assert _run(["delete-project", "--user", "Ken", "--title", "NoProj"]) == 1


# -----------------------------------------------------------------------
# task command tests
# -----------------------------------------------------------------------

class TestTaskCommands:
    def _setup(self, uname="Eve", pname="Proj"):
        """Helper to create a user with a project already added"""
        u = User(name=uname)
        p = Project(title=pname, owner=uname)
        u.add_project(p)
        User.register(u)
        return u, p

    def test_add_task_success(self):
        _, p = self._setup()
        assert _run(["add-task", "--project", "Proj", "--title", "T1", "--user", "Eve"]) == 0
        assert p.get_task("T1") is not None

    def test_add_task_assignee(self):
        _, p = self._setup()
        _run(["add-task", "--project", "Proj", "--title", "T2",
              "--assigned-to", "Eve", "--user", "Eve"])
        assert p.get_task("T2").assigned_to == "Eve"

    def test_add_task_unknown_project_fails(self):
        assert _run(["add-task", "--project", "Ghost", "--title", "T"]) == 1

    def test_add_duplicate_task_fails(self):
        _, _ = self._setup()
        _run(["add-task", "--project", "Proj", "--title", "Dup", "--user", "Eve"])
        assert _run(["add-task", "--project", "Proj", "--title", "Dup", "--user", "Eve"]) == 1

    def test_list_tasks_success(self):
        u, p = self._setup("Lily", "LP")
        p.add_task(Task(title="LT"))
        assert _run(["list-tasks", "--project", "LP", "--user", "Lily"]) == 0

    def test_list_tasks_unknown_project_fails(self):
        assert _run(["list-tasks", "--project", "NoProj"]) == 1

    def test_complete_task(self):
        _, p = self._setup("Frank", "SP")
        p.add_task(Task(title="ST"))
        _run(["complete-task", "--project", "SP", "--task", "ST", "--user", "Frank"])
        assert p.get_task("ST").status == "complete"

    def test_start_task(self):
        _, p = self._setup("Gail", "GP")
        p.add_task(Task(title="GT"))
        _run(["start-task", "--project", "GP", "--task", "GT", "--user", "Gail"])
        assert p.get_task("GT").status == "in_progress"

    def test_complete_unknown_task_fails(self):
        self._setup("Hal", "HP")
        assert _run(["complete-task", "--project", "HP", "--task", "Ghost", "--user", "Hal"]) == 1

    def test_complete_unknown_project_fails(self):
        assert _run(["complete-task", "--project", "NoProj", "--task", "T"]) == 1

    def test_delete_task_success(self):
        _, p = self._setup("Iris", "IP")
        p.add_task(Task(title="Del"))
        assert _run(["delete-task", "--project", "IP", "--task", "Del", "--user", "Iris"]) == 0
        assert p.get_task("Del") is None

    def test_delete_unknown_task_fails(self):
        self._setup("Jan", "JP")
        assert _run(["delete-task", "--project", "JP", "--task", "Ghost", "--user", "Jan"]) == 1


# -----------------------------------------------------------------------
# Validator tests
# -----------------------------------------------------------------------

class TestValidators:
    def test_valid_email(self):
        from utils.validators import validate_email
        assert validate_email("u@d.com") == "u@d.com"

    def test_empty_email_ok(self):
        from utils.validators import validate_email
        assert validate_email("") == ""

    def test_invalid_email_raises(self):
        from utils.validators import validate_email
        with pytest.raises(ValueError):
            validate_email("bad")

    def test_valid_date_iso(self):
        from utils.validators import validate_date
        assert validate_date("2025-12-31") == "2025-12-31"

    def test_empty_date_ok(self):
        from utils.validators import validate_date
        assert validate_date("") == ""

    def test_natural_language_date(self):
        from utils.validators import validate_date
        assert validate_date("December 31 2025") == "2025-12-31"
