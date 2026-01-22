"""
Level 2: Exception Testing
===========================
Goal: Test that code raises expected exceptions for invalid input.

Focus: 4 practical tests for validating error handling in FastAPI apps.

Run these tests:
    pytest tests/unit/test_level_2_exceptions.py -v
    pytest -k level_2 -v
"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from project.config import Settings
from project.db.models.task import TaskCreate
from project.exceptions import AuthenticationError, EntityNotFoundError
from project.utils.pagination import PaginationParams


@pytest.mark.unit
@pytest.mark.level_2
class TestLevel2:
    """
    Level 2: Exception Testing

    These 5 tests cover essential exception testing patterns:
    1. Pydantic validation rejects invalid input
    2. Boundary validation (min/max values)
    3. Config/Settings validation
    4. Domain exception raising and catching
    """

    # =========================================================================
    # TEST 1: Pydantic Rejects Invalid Input
    # WHY: Your API should return 422 for invalid payloads, not crash
    # =========================================================================
    def test_task_create_rejects_empty_title(self):
        """Test that TaskCreate raises ValidationError for empty title.

        Real-world: Clients might send {"title": ""} which should fail
        validation, not create a task with empty title.
        """
        with pytest.raises(PydanticValidationError) as exc_info:
            TaskCreate(title="")

        # verify it's the title field that failed
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("title",) for e in errors)

    # =========================================================================
    # TEST 2: Boundary Validation
    # WHY: Test edge cases - what values are just inside/outside valid range
    # =========================================================================
    def test_pagination_boundary_validation(self):
        """Test pagination params enforce min/max boundaries.

        Real-world: Clients might request limit=0, limit=9999, or offset=-1.
        Your API needs to reject these before hitting the database.
        """
        # limit must be > 0
        with pytest.raises(PydanticValidationError):
            PaginationParams(limit=0)

        # limit must be <= 100
        with pytest.raises(PydanticValidationError):
            PaginationParams(limit=101)

        # offset must be >= 0
        with pytest.raises(PydanticValidationError) as exc_info:
            PaginationParams(offset=-1)

        errors = exc_info.value.errors()
        assert errors[0]["loc"] == ("offset",)

        # boundary values should work
        valid_min = PaginationParams(limit=1, offset=0)
        valid_max = PaginationParams(limit=100, offset=1000)
        assert valid_min.limit == 1
        assert valid_max.limit == 100

    # TODO: example subclass

    # =========================================================================
    # TEST 3: Config/Settings Validation
    # WHY: App should fail fast on bad config, not at runtime
    # =========================================================================
    def test_settings_rejects_invalid_config(self):
        """Test Settings validation catches config errors at startup.

        Real-world: If DB_URL is empty or token expiry is negative,
        the app should fail immediately, not when first user logs in.
        """
        # empty DB_URL should fail
        with pytest.raises(ValueError):
            Settings(
                SECRET_KEY="test",
                DB_URL="",
                DB_TYPE="sqlite",
            )

        # negative token expiry should fail
        with pytest.raises(ValueError):
            Settings(
                SECRET_KEY="test",
                DB_URL="sqlite:///test.db",
                DB_TYPE="sqlite",
                ACCESS_TOKEN_EXPIRE_MINUTES=-1,
            )

    # =========================================================================
    # TEST 4: Domain Exception Raising and Catching
    # WHY: Services raise domain exceptions, routers catch and convert to HTTP
    # =========================================================================
    def test_service_function_raises_domain_exception(self):
        """Test that domain exceptions can be raised and caught correctly.

        Real-world: Your services raise EntityNotFoundError, your routers
        catch it and return HTTP 404. This pattern must work.
        """

        def lookup_task(task_id: str):
            # simulate service that doesn't find the entity
            raise EntityNotFoundError("Task", task_id)

        # exception is raiseable
        with pytest.raises(EntityNotFoundError) as exc_info:
            lookup_task("nonexistent-uuid")

        # exception has expected attributes for error handling
        assert exc_info.value.entity_type == "Task"
        assert exc_info.value.identifier == "nonexistent-uuid"

        # exception is catchable by parent class
        try:
            lookup_task("another-uuid")
        except Exception as e:
            from project.exceptions import ServiceError

            assert isinstance(e, ServiceError)


# =============================================================================
# EXERCISES - Practice exception testing patterns
# =============================================================================


@pytest.mark.unit
@pytest.mark.level_2
class TestLevel2Exercises:
    """
    Exercises: Apply what you learned above.

    Complete these tests following the same patterns.
    """

    def test_task_priority_boundaries(self):
        """Exercise: Test TaskCreate priority must be 1-5.

        - priority=0 should raise PydanticValidationError
        - priority=6 should raise PydanticValidationError
        - priority=1 and priority=5 should work (boundary values)
        """
        with pytest.raises(PydanticValidationError):
            TaskCreate(title="Test", priority=0)

        with pytest.raises(PydanticValidationError):
            TaskCreate(title="Test", priority=6)

        task_prio_1 = TaskCreate(title="Test", priority=1)
        task_prio_5 = TaskCreate(title="Test", priority=5)

        assert task_prio_1.title == "Test"
        assert task_prio_1.priority == 1
        assert task_prio_5.title == "Test"
        assert task_prio_5.priority == 5

    def test_task_title_max_length(self):
        """Exercise: Test TaskCreate title max length is 200 chars.

        - title with 201 chars should raise PydanticValidationError
        - title with exactly 200 chars should work

        Hint: "x" * 201 creates a string of 201 x's
        """
        with pytest.raises(PydanticValidationError):
            TaskCreate(title="A" * 201)

        task = TaskCreate(title="B" * 200)
        assert task.title == "B" * 200

    def test_exception_context_contains_details(self):
        """Exercise: Test that exception context dict has useful info.

        Create an EntityNotFoundError("User", "test@example.com") and verify:
        - error.context is a dict
        - error.context["entity_type"] == "User"
        - error.context["identifier"] == "test@example.com"
        """
        error = EntityNotFoundError("User", "test@example.com")
        assert isinstance(error.context, dict)
        assert error.context["entity_type"] == "User"
        assert error.context["identifier"] == "test@example.com"
