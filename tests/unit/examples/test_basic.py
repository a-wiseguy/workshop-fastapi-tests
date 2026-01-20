"""
Level 1: Simple Assertion Tests
================================
Goal: Test pure functions and Pydantic models with basic assertions.

These tests verify:
- Default values work as expected
- Data models validate input correctly
- Pure functions return expected outputs

Run these tests:
    pytest tests/unit/test_level_1_basics.py -v
    pytest -k level_1 -v
"""

import pytest

from project.db.models.task import TaskCreate, TaskStatus
from project.exceptions import EntityNotFoundError, ServiceError
from project.security import encrypt_password
from project.utils.pagination import (
    PaginationParams,
    calculate_total_pages,
)

# =============================================================================
# EXAMPLE TESTS - Study these patterns
# =============================================================================


@pytest.mark.unit
@pytest.mark.level_1
class TestPaginationParamsDefaults:
    """Example: Test Pydantic model default values."""

    def test_pagination_params_has_correct_defaults(self):
        """Test that PaginationParams has sensible defaults."""
        params = PaginationParams()

        assert params.limit == 10
        assert params.offset == 0
        assert params.sort_order == "asc"

    def test_pagination_params_accepts_custom_values(self):
        """Test that custom values override defaults."""
        params = PaginationParams(limit=25, offset=50, sort_order="desc")

        assert params.limit == 25
        assert params.offset == 50
        assert params.sort_order == "desc"


@pytest.mark.unit
@pytest.mark.level_1
class TestTaskCreateSchema:
    """Example: Test Pydantic schema validation."""

    def test_task_create_with_minimal_fields(self):
        """Test TaskCreate with only required fields."""
        task = TaskCreate(title="My Task")

        assert task.title == "My Task"
        assert task.description is None
        assert task.status == TaskStatus.TODO
        assert task.priority == 3  # default

    def test_task_create_with_all_fields(self):
        """Test TaskCreate with all fields specified."""
        task = TaskCreate(
            title="Complete Task",
            description="Full description",
            status=TaskStatus.IN_PROGRESS,
            priority=5,
        )

        assert task.title == "Complete Task"
        assert task.description == "Full description"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == 5


@pytest.mark.unit
@pytest.mark.level_1
class TestPasswordEncryption:
    """Example: Test pure function behavior."""

    def test_encrypt_password_returns_string(self):
        """Encrypted password should be a string."""
        result = encrypt_password("mypassword")

        assert isinstance(result, str)

    def test_encrypt_password_differs_from_input(self):
        """Encrypted password should not equal original."""
        password = "mypassword"
        encrypted = encrypt_password(password)

        assert encrypted != password

    def test_encrypt_password_produces_different_hashes(self):
        """Same password should produce different hashes (due to salt)."""
        password = "mypassword"

        hash1 = encrypt_password(password)
        hash2 = encrypt_password(password)

        # bcrypt salts produce unique hashes
        assert hash1 != hash2


@pytest.mark.unit
@pytest.mark.level_1
class TestExceptionMessageFormatting:
    """Example: Test exception classes format messages correctly."""

    def test_entity_not_found_message_with_identifier(self):
        """EntityNotFoundError includes identifier in message."""
        error = EntityNotFoundError("User", "john@example.com")

        assert "User" in error.message
        assert "john@example.com" in error.message

    def test_entity_not_found_message_without_identifier(self):
        """EntityNotFoundError works without identifier."""
        error = EntityNotFoundError("Task")

        assert error.message == "Task not found"
        assert error.identifier is None

    def test_service_error_stores_context(self):
        """ServiceError stores context dictionary."""
        context = {"user_id": "123", "action": "delete"}
        error = ServiceError("Operation failed", context=context)

        assert error.context == context


# =============================================================================
# EXERCISES - Complete these tests
# =============================================================================


@pytest.mark.unit
@pytest.mark.level_1
class TestPaginationHelpers:
    """Exercise: Test pagination helper functions."""

    def test_calculate_total_pages_exact_division(self):
        """TODO: Test calculate_total_pages when total divides evenly by limit."""
        # given: 100 items with limit of 10
        # expect: 10 pages
        total_pages = calculate_total_pages(total=100, limit=10)
        assert total_pages == 10

    def test_calculate_total_pages_with_remainder(self):
        """TODO: Test calculate_total_pages when there's a remainder."""
        # given: 25 items with limit of 10
        # expect: 3 pages (10 + 10 + 5)
        # YOUR CODE HERE
        pass

    def test_has_next_page_returns_true_when_more_items(self):
        """TODO: Test has_next_page returns True when more items exist."""
        # given: total=50, offset=0, limit=10
        # expect: True (more pages available)
        # YOUR CODE HERE
        pass

    def test_has_next_page_returns_false_on_last_page(self):
        """TODO: Test has_next_page returns False on last page."""
        # given: total=50, offset=40, limit=10
        # expect: False (this is the last page)
        # YOUR CODE HERE
        pass

    def test_has_previous_page_returns_false_on_first_page(self):
        """TODO: Test has_previous_page returns False when offset is 0."""
        # YOUR CODE HERE
        pass


@pytest.mark.unit
@pytest.mark.level_1
class TestTaskStatusEnum:
    """Exercise: Test TaskStatus enum values."""

    def test_task_status_has_expected_values(self):
        """TODO: Verify TaskStatus enum has todo, in_progress, done values."""
        # check that these values exist:
        # - TaskStatus.TODO
        # - TaskStatus.IN_PROGRESS
        # - TaskStatus.DONE
        # YOUR CODE HERE
        pass

    def test_task_status_values_are_lowercase(self):
        """TODO: Verify enum .value attributes are lowercase strings."""
        # YOUR CODE HERE
        pass


@pytest.mark.unit
@pytest.mark.level_1
class TestUserResponseSchema:
    """Exercise: Test UserResponse from_attributes works."""

    def test_user_response_from_attributes_with_fixture(self, sample_user):
        """TODO: Test UserResponse.model_validate() works with User object."""
        # use the sample_user fixture
        # convert to UserResponse using model_validate()
        # assert fields match
        # YOUR CODE HERE
        pass


@pytest.mark.unit
@pytest.mark.level_1
class TestRoleEnum:
    """Exercise: Test Role enum."""

    def test_role_has_admin_and_user(self):
        """TODO: Verify Role enum has ADMIN and USER values."""
        # YOUR CODE HERE
        pass


@pytest.mark.unit
@pytest.mark.level_1
class TestValidationErrorContext:
    """Exercise: Test ValidationError stores field info."""

    def test_validation_error_stores_field(self):
        """TODO: Test ValidationError stores field name in context."""
        # create ValidationError with field="email"
        # verify error.field == "email"
        # verify error.context contains the field
        # YOUR CODE HERE
        pass
