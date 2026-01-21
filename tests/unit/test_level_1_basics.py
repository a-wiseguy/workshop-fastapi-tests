"""
Level 1: Simple Assertion Tests
================================
Goal: Test pure functions and Pydantic models with basic assertions.

Focus: 4 practical tests you'll use daily in FastAPI development.

Run these tests:
    pytest tests/unit/test_level_1_basics.py -v
    pytest -k level_1 -v
"""

import pytest

from project.db.models.task import TaskCreate, TaskResponse, TaskStatus
from project.db.models.user import Role, UserResponse
from project.exceptions import EntityNotFoundError
from project.security import encrypt_password, verify_password


@pytest.mark.unit
@pytest.mark.level_1
class TestLevel1:
    """
    Level 1: Simple Assertion Tests

    These 4 tests cover the most common unit testing scenarios in FastAPI apps:
    1. Pydantic schema defaults and required fields
    2. Password hashing security
    3. ORM to Response schema conversion (model_validate)
    4. Domain exception message formatting
    """

    # =========================================================================
    # TEST 1: Pydantic Schema Defaults
    # WHY: Ensures your API accepts minimal payloads and applies sensible defaults
    # =========================================================================
    def test_task_create_schema_applies_defaults(self):
        """Test that TaskCreate applies correct defaults for optional fields.

        Real-world: Clients often send minimal JSON payloads. Your schema
        must fill in sensible defaults for fields they don't provide.
        """
        task = TaskCreate(title="Fix login bug")

        # required field is set
        assert task.title == "Fix login bug"

        # optional fields have sensible defaults
        assert task.description is None
        assert task.status == TaskStatus.TODO
        assert task.priority == 3
        assert task.assigned_to is None

    # =========================================================================
    # TEST 2: Password Hashing Security
    # WHY: Critical security test - passwords must be hashed, never stored plain
    # =========================================================================
    def test_password_encryption_is_secure(self):
        """Test that password encryption produces verifiable, unique hashes.

        Real-world: Never store plain passwords. This test verifies:
        - Hash differs from input (encrypted)
        - Same password produces different hashes (salted)
        - Original password can be verified against hash
        """
        password = "secretPassword123"

        # encrypt twice
        hash1 = encrypt_password(password)
        hash2 = encrypt_password(password)

        # hashes differ from input
        assert hash1 != password
        assert hash2 != password

        # hashes differ from each other (salted)
        assert hash1 != hash2

        # but both verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
        assert verify_password("wrongpassword", hash1) is False

    # =========================================================================
    # TEST 3: ORM to Response Schema Conversion
    # WHY: Ensures model_validate works with your ORM objects
    # =========================================================================
    def test_response_schema_from_orm_object(self, sample_user):
        """Test UserResponse.model_validate() converts ORM objects correctly.

        Real-world: In routers you convert ORM objects to response schemas:
            return UserResponse.model_validate(db_user)

        This test verifies from_attributes=True works with your models.
        """
        # sample_user is a Mock with ORM-like attributes
        response = UserResponse.model_validate(sample_user)

        assert response.uuid == sample_user.uuid
        assert response.username == sample_user.username
        assert response.email == sample_user.email
        assert response.role == sample_user.role

    # =========================================================================
    # TEST 4: Domain Exception Formatting
    # WHY: Ensures your error responses contain useful debugging info
    # =========================================================================
    def test_entity_not_found_exception_formatting(self):
        """Test EntityNotFoundError formats message with context.

        Real-world: When a lookup fails, your error message should identify:
        - What type of entity was not found
        - What identifier was used in the lookup

        This helps debugging in logs and API error responses.
        """
        error = EntityNotFoundError("User", "john@example.com")

        # message contains entity type and identifier
        assert "User" in error.message
        assert "john@example.com" in error.message

        # attributes are accessible for error handlers
        assert error.entity_type == "User"
        assert error.identifier == "john@example.com"

        # context dict available for structured logging
        assert error.context["entity_type"] == "User"
        assert error.context["identifier"] == "john@example.com"


# =============================================================================
# EXERCISES - Practice writing these patterns
# =============================================================================


@pytest.mark.unit
@pytest.mark.level_1
class TestLevel1Exercises:
    """
    Exercises: Apply what you learned above.

    Complete these tests following the same patterns.
    """

    def test_task_create_with_all_fields(self):
        """Exercise: Test TaskCreate accepts all optional fields.

        Create a TaskCreate with title, description, status=IN_PROGRESS,
        priority=5, and verify all fields are set correctly.
        """
        task = TaskCreate(
            title="title",
            description="description",
            status=TaskStatus.IN_PROGRESS,
            priority=5,
        )

        assert task.title == "title"
        assert task.description == "description"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == 5
        assert task.assigned_to is None

    def test_task_response_schema_from_task_mock(self, sample_task):
        """Exercise: Test TaskResponse.model_validate() with sample_task fixture.

        Convert sample_task to TaskResponse and verify fields match.
        """
        response = TaskResponse.model_validate(sample_task)

        assert response.uuid == sample_task.uuid
        assert response.title == sample_task.title
        assert response.description == sample_task.description
        assert response.status == sample_task.status
        assert response.priority == sample_task.priority
        assert response.due_date == sample_task.due_date
        assert response.created_by == sample_task.created_by
        assert response.assigned_to == sample_task.assigned_to
        assert response.created_at == sample_task.created_at

    def test_entity_not_found_without_identifier(self):
        """Exercise: Test EntityNotFoundError with only entity_type.

        Create error with just "Task" (no identifier) and verify:
        - message is "Task not found"
        - identifier is None
        """

        error = EntityNotFoundError("Task")

        assert "Task not found" in error.message

        assert error.identifier == None
