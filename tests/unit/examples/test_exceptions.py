"""
Level 2: Exception Testing
===========================
Goal: Test that functions raise expected exceptions and side effects.

Key concepts:
- pytest.raises() context manager
- Checking exception messages and attributes
- Testing validation boundaries

Run these tests:
    pytest tests/unit/test_level_2_exceptions.py -v
    pytest -k level_2 -v
"""

import pytest
from pydantic import ValidationError as PydanticValidationError

from project.db.models.task import TaskCreate
from project.exceptions import EntityNotFoundError
from project.utils.pagination import PaginationParams

# =============================================================================
# EXAMPLE TESTS - Study these patterns
# =============================================================================


@pytest.mark.unit
@pytest.mark.level_2
class TestPaginationParamsValidation:
    """Example: Test Pydantic validation raises on invalid input."""

    def test_pagination_rejects_negative_offset(self):
        """PaginationParams should reject negative offset."""
        with pytest.raises(PydanticValidationError) as exc_info:
            PaginationParams(offset=-1)

        # check error details
        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("offset",)

    def test_pagination_rejects_zero_limit(self):
        """PaginationParams should reject zero limit."""
        with pytest.raises(PydanticValidationError) as exc_info:
            PaginationParams(limit=0)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("limit",) for e in errors)

    def test_pagination_rejects_excessive_limit(self):
        """PaginationParams should reject limit > 100."""
        with pytest.raises(PydanticValidationError):
            PaginationParams(limit=101)


@pytest.mark.unit
@pytest.mark.level_2
class TestTaskCreateValidation:
    """Example: Test TaskCreate schema validation boundaries."""

    def test_task_create_rejects_empty_title(self):
        """TaskCreate should reject empty title."""
        with pytest.raises(PydanticValidationError) as exc_info:
            TaskCreate(title="")

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("title",) for e in errors)

    def test_task_create_rejects_priority_below_1(self):
        """TaskCreate should reject priority < 1."""
        with pytest.raises(PydanticValidationError):
            TaskCreate(title="Test", priority=0)

    def test_task_create_rejects_priority_above_5(self):
        """TaskCreate should reject priority > 5."""
        with pytest.raises(PydanticValidationError):
            TaskCreate(title="Test", priority=6)

    def test_task_create_accepts_boundary_priorities(self):
        """TaskCreate should accept priority 1 and 5."""
        # these should NOT raise
        task_low = TaskCreate(title="Low Priority", priority=1)
        task_high = TaskCreate(title="High Priority", priority=5)

        assert task_low.priority == 1
        assert task_high.priority == 5


@pytest.mark.unit
@pytest.mark.level_2
class TestEntityNotFoundError:
    """Example: Test custom exception behavior."""

    def test_entity_not_found_is_service_error(self):
        """EntityNotFoundError should be a ServiceError subclass."""
        error = EntityNotFoundError("User", "123")

        # isinstance checks inheritance
        from project.exceptions import ServiceError

        assert isinstance(error, ServiceError)

    def test_entity_not_found_stores_entity_type(self):
        """EntityNotFoundError should store entity_type attribute."""
        error = EntityNotFoundError("Task", "abc-123")

        assert error.entity_type == "Task"
        assert error.identifier == "abc-123"

    def test_entity_not_found_can_be_raised_and_caught(self):
        """EntityNotFoundError should be raiseable and catchable."""

        def lookup_user(user_id: str):
            raise EntityNotFoundError("User", user_id)

        with pytest.raises(EntityNotFoundError) as exc_info:
            lookup_user("nonexistent")

        assert exc_info.value.entity_type == "User"


# =============================================================================
# EXERCISES - Complete these tests
# =============================================================================


@pytest.mark.unit
@pytest.mark.level_2
class TestSettingsValidation:
    """Exercise: Test Settings validation raises on invalid config."""

    def test_settings_rejects_empty_db_url(self):
        """TODO: Test Settings raises when DB_URL is empty."""
        # use pytest.raises to verify ValueError is raised
        # when creating Settings(DB_URL="")
        # YOUR CODE HERE
        pass

    def test_settings_rejects_invalid_db_url_format(self):
        """TODO: Test Settings raises on non-sqlite:// URL when DB_TYPE is sqlite."""
        # when DB_TYPE="sqlite", the DB_URL should start with "sqlite://"
        # test that an invalid format raises an error
        # YOUR CODE HERE
        pass

    def test_settings_rejects_negative_token_expiry(self):
        """TODO: Test Settings raises when ACCESS_TOKEN_EXPIRE_MINUTES <= 0."""
        # YOUR CODE HERE
        pass


@pytest.mark.unit
@pytest.mark.level_2
class TestAuthenticationError:
    """Exercise: Test AuthenticationError exception."""

    def test_authentication_error_has_default_message(self):
        """TODO: Test AuthenticationError has sensible default message."""
        # create AuthenticationError without arguments
        # verify it has a default message
        # YOUR CODE HERE
        pass

    def test_authentication_error_accepts_custom_message(self):
        """TODO: Test AuthenticationError stores custom message."""
        # YOUR CODE HERE
        pass


@pytest.mark.unit
@pytest.mark.level_2
class TestAuthorizationError:
    """Exercise: Test AuthorizationError exception."""

    def test_authorization_error_stores_required_role(self):
        """TODO: Test AuthorizationError stores required_role attribute."""
        # create AuthorizationError with required_role="admin"
        # verify error.required_role == "admin"
        # verify error.context contains required_role
        # YOUR CODE HERE
        pass


@pytest.mark.unit
@pytest.mark.level_2
class TestValidationErrorField:
    """Exercise: Test ValidationError with field context."""

    def test_validation_error_includes_field_in_context(self):
        """TODO: Test ValidationError field is in context dict."""
        # create ValidationError("Invalid email", field="email")
        # verify error.context["field"] == "email"
        # YOUR CODE HERE
        pass

    def test_validation_error_without_field(self):
        """TODO: Test ValidationError works without field argument."""
        # create ValidationError with just message
        # verify error.field is None
        # verify error.context does not contain "field" key
        # YOUR CODE HERE
        pass


@pytest.mark.unit
@pytest.mark.level_2
class TestTaskCreateTitleValidation:
    """Exercise: Test TaskCreate title length limits."""

    def test_task_create_rejects_title_over_200_chars(self):
        """TODO: Test TaskCreate rejects title longer than 200 characters."""
        # create a title with 201 characters
        # verify PydanticValidationError is raised
        # YOUR CODE HERE
        pass

    def test_task_create_accepts_title_at_max_length(self):
        """TODO: Test TaskCreate accepts exactly 200 character title."""
        # create a title with exactly 200 characters
        # verify it works without raising
        # YOUR CODE HERE
        pass
