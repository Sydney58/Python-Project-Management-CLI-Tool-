"""
test_models.py - Unit tests for all the model classes

The professor said we need tests so here they are lol.
I actually found writing tests really useful though - caught a few bugs
I wouldn't have noticed otherwise (like the duplicate task check being
case-sensitive when it shouldn't be).

Run with: pytest tests/ -v
"""
import pytest

from models.person import Person
from models.task import Task
from models.project import Project
from models.user import User


# -----------------------------------------------------------------------
# Person tests
# -----------------------------------------------------------------------


class TestPerson:
    """Tests for the Person base class"""

    def test_basic_creation(self):
        """Should be able to create a Person with name and email"""
        p = Person(name="Alice", email="alice@example.com")
        assert p.name == "Alice"
        assert p.email == "alice@example.com"

    def test_name_stripped(self):
        """Extra whitespace in the name should be automatically removed"""
        p = Person(name="  Bob  ")
        assert p.name == "Bob"

    def test_name_setter_valid(self):
        """Should be able to update the name after creation"""
        p = Person(name="Carol")
        p.name = "Carol Updated"
        assert p.name == "Carol Updated"

    def test_name_setter_empty_raises(self):
        """Setting name to empty string should raise ValueError"""
        p = Person(name="Dave")
        with pytest.raises(ValueError, match="Name cannot be empty"):
            p.name = "   "

    def test_str_with_email(self):
        """__str__ should include both name and email when email is set"""
        p = Person(name="Eve", email="eve@example.com")
        assert "Eve" in str(p)
        assert "eve@example.com" in str(p)

    def test_str_without_email(self):
        """__str__ should just return the name if no email"""
        p = Person(name="Frank")
        assert str(p) == "Frank"

    def test_to_dict(self):
        """to_dict should return a dict with name and email keys"""
        p = Person(name="Grace", email="grace@test.com")
        d = p.to_dict()
        assert d["name"] == "Grace"
        assert d["email"] == "grace@test.com"


# -----------------------------------------------------------------------
# Task tests
# -----------------------------------------------------------------------


class TestTask:
    """Tests for the Task model"""

    def test_default_status_is_pending(self):
        """New tasks should start with 'pending' status"""
        t = Task(title="Write docs")
        assert t.status == "pending"

    def test_mark_complete(self):
        """mark_complete() should set status to 'complete'"""
        t = Task(title="Deploy app")
        t.mark_complete()
        assert t.status == "complete"

    def test_mark_in_progress(self):
        """mark_in_progress() should set status to 'in_progress'"""
        t = Task(title="Review PR")
        t.mark_in_progress()
        assert t.status == "in_progress"

    def test_invalid_status_raises(self):
        """Creating a task with a made-up status should fail"""
        with pytest.raises(ValueError, match="Invalid status"):
            Task(title="Bad status task", status="done")

    def test_empty_title_raises(self):
        """Tasks must have a title - empty string should raise ValueError"""
        with pytest.raises(ValueError, match="title cannot be empty"):
            Task(title="")

    def test_assigned_to_stripped(self):
        """Whitespace should be stripped from the assigned_to field"""
        t = Task(title="T", assigned_to="  Alex  ")
        assert t.assigned_to == "Alex"

    def test_to_dict(self):
        """to_dict should include all the task fields"""
        t = Task(title="Test serialise", assigned_to="Alex", status="in_progress")
        d = t.to_dict()
        assert d["title"] == "Test serialise"
        assert d["assigned_to"] == "Alex"
        assert d["status"] == "in_progress"
        assert "id" in d

    def test_from_dict_roundtrip(self):
        """Saving and reloading a task should give back the same data"""
        original = Task(title="Roundtrip task", assigned_to="Beth", status="complete")
        restored = Task.from_dict(original.to_dict())
        assert restored.title == original.title
        assert restored.status == original.status
        assert restored.assigned_to == original.assigned_to
        assert restored.id == original.id

    def test_str_representation(self):
        """__str__ should show the status and title"""
        t = Task(title="Deploy")
        assert "PENDING" in str(t)
        assert "Deploy" in str(t)


# -----------------------------------------------------------------------
# Project tests
# -----------------------------------------------------------------------


class TestProject:
    """Tests for the Project model"""

    def _project(self) -> Project:
        """Helper to create a test project without repeating myself"""
        return Project(title="Alpha", owner="Alex", description="Test project")

    def test_creation(self):
        """Project should store title, owner, and description correctly"""
        p = self._project()
        assert p.title == "Alpha"
        assert p.owner == "Alex"
        assert p.description == "Test project"

    def test_add_task(self):
        """Should be able to add tasks to a project"""
        p = self._project()
        t = Task(title="First task")
        p.add_task(t)
        assert len(p.tasks) == 1
        assert p.tasks[0].title == "First task"

    def test_duplicate_task_raises(self):
        """Adding a task with the same title should fail (case-insensitive)"""
        p = self._project()
        p.add_task(Task(title="Dup"))
        with pytest.raises(ValueError, match="already exists"):
            p.add_task(Task(title="dup"))  # lowercase should still be caught

    def test_get_task(self):
        """get_task should find by title and return None if missing"""
        p = self._project()
        t = Task(title="Find me")
        p.add_task(t)
        assert p.get_task("find me") is t  # case-insensitive lookup
        assert p.get_task("missing") is None

    def test_remove_task(self):
        """remove_task should return True on success, False if task not found"""
        p = self._project()
        p.add_task(Task(title="Remove me"))
        assert p.remove_task("Remove me") is True
        assert len(p.tasks) == 0
        assert p.remove_task("ghost") is False  # already gone

    def test_completion_rate_empty(self):
        """Completion rate should be 0.0 when there are no tasks"""
        p = self._project()
        assert p.completion_rate == 0.0

    def test_completion_rate_partial(self):
        """1 of 2 tasks complete = 50%"""
        p = self._project()
        t1 = Task(title="T1")
        t2 = Task(title="T2")
        t1.mark_complete()
        p.add_task(t1)
        p.add_task(t2)
        assert p.completion_rate == 50.0

    def test_completion_rate_all_done(self):
        """All tasks complete = 100%"""
        p = self._project()
        for i in range(3):
            t = Task(title=f"T{i}")
            t.mark_complete()
            p.add_task(t)
        assert p.completion_rate == 100.0

    def test_find_by_title(self):
        """find_by_title class method should work case-insensitively"""
        projects = [Project(title="A", owner="u"), Project(title="B", owner="u")]
        assert Project.find_by_title(projects, "b") is projects[1]
        assert Project.find_by_title(projects, "C") is None

    def test_to_dict_includes_tasks(self):
        """to_dict should include the tasks list"""
        p = self._project()
        p.add_task(Task(title="Task A"))
        d = p.to_dict()
        assert len(d["tasks"]) == 1
        assert d["tasks"][0]["title"] == "Task A"

    def test_from_dict_roundtrip(self):
        """Save and reload a project - should get back the same data"""
        original = Project(title="Beta", owner="Beth", due_date="2025-01-01")
        original.add_task(Task(title="Sub-task"))
        restored = Project.from_dict(original.to_dict())
        assert restored.title == original.title
        assert restored.owner == original.owner
        assert len(restored.tasks) == 1

    def test_empty_title_raises(self):
        """Project title can't be empty"""
        with pytest.raises(ValueError):
            Project(title="", owner="u")

    def test_empty_owner_raises(self):
        """Project must have an owner"""
        with pytest.raises(ValueError):
            Project(title="T", owner="")


# -----------------------------------------------------------------------
# User tests
# -----------------------------------------------------------------------


class TestUser:
    """Tests for the User model"""

    def setup_method(self):
        """Clear the registry before each test so they don't affect each other"""
        User.clear_registry()

    def _user(self, name="Alice", email="alice@test.com") -> User:
        """Helper to make a user quickly"""
        return User(name=name, email=email)

    def test_creation(self):
        """User should be created with correct name, email, and empty projects list"""
        u = self._user()
        assert u.name == "Alice"
        assert u.email == "alice@test.com"
        assert u.projects == []

    def test_add_project(self):
        """Should be able to add a project to a user"""
        u = self._user()
        p = Project(title="P1", owner="Alice")
        u.add_project(p)
        assert len(u.projects) == 1

    def test_duplicate_project_raises(self):
        """Can't have two projects with the same title under the same user"""
        u = self._user()
        u.add_project(Project(title="Same", owner="Alice"))
        with pytest.raises(ValueError, match="already exists"):
            u.add_project(Project(title="same", owner="Alice"))

    def test_get_project(self):
        """get_project should find the project or return None"""
        u = self._user()
        p = Project(title="FindMe", owner="Alice")
        u.add_project(p)
        assert u.get_project("findme") is p  # case-insensitive
        assert u.get_project("missing") is None

    def test_remove_project(self):
        """remove_project should return True if found, False otherwise"""
        u = self._user()
        u.add_project(Project(title="Bye", owner="Alice"))
        assert u.remove_project("Bye") is True
        assert len(u.projects) == 0
        assert u.remove_project("Ghost") is False

    def test_registry_find(self):
        """User.find() should locate a registered user by name"""
        u = self._user()
        User.register(u)
        found = User.find("alice")
        assert found is u

    def test_registry_all_users(self):
        """User.all_users() should return everyone in the registry"""
        u1 = self._user("Alice")
        u2 = self._user("Bob", "bob@test.com")
        User.register(u1)
        User.register(u2)
        all_u = User.all_users()
        assert len(all_u) == 2

    def test_inherits_person(self):
        """User should be an instance of Person (checking inheritance works)"""
        from models.person import Person
        u = self._user()
        assert isinstance(u, Person)

    def test_to_dict_includes_projects(self):
        """to_dict should include nested projects and their tasks"""
        u = self._user()
        p = Project(title="Proj", owner="Alice")
        p.add_task(Task(title="Task"))
        u.add_project(p)
        d = u.to_dict()
        assert d["name"] == "Alice"
        assert len(d["projects"]) == 1
        assert len(d["projects"][0]["tasks"]) == 1

    def test_from_dict_roundtrip(self):
        """Save and reload a user - should get back the same data"""
        original = self._user()
        original.add_project(Project(title="P", owner="Alice"))
        restored = User.from_dict(original.to_dict())
        assert restored.name == original.name
        assert restored.email == original.email
        assert len(restored.projects) == 1
