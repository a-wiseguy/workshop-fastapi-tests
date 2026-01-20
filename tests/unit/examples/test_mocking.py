"""
Level 3: Mocking and Patching
==============================
Goal: Isolate units under test using unittest.mock.

Key concepts:
- Mock objects to replace dependencies
- patch() to temporarily replace imports
- MagicMock for automatic method/attribute creation
- Verifying call counts and arguments

Run these tests:
    pytest tests/unit/test_level_3_mocking.py -v
    pytest -k level_3 -v
"""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from project.db.models.task import Task
from project.db.models.user import User
from project.exceptions import EntityNotFoundError
from project.security import TokenPayload, create_access_token, verify_password
from project.utils.pagination import PaginatedData, PaginationParams

# =============================================================================
# EXAMPLE TESTS - Study these patterns
# =============================================================================


@pytest.mark.unit
@pytest.mark.level_3
class TestServiceWithMockedSession:
    """Example: Mock SQLAlchemy Session to test service functions."""

    def test_get_user_by_username_with_mock_session(self):
        """Test user lookup with mocked database session."""
        # arrange: create mock session and user
        mock_session = Mock()
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"

        # configure mock to return user
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        # act: call the service function
        from project.services.user_service import get_user_by_username

        result = get_user_by_username(mock_session, "testuser")

        # assert: verify result and that session was called correctly
        assert result.username == "testuser"
        mock_session.execute.assert_called_once()

    def test_get_user_by_username_raises_when_not_found(self):
        """Test that service raises EntityNotFoundError when user missing."""
        # arrange: mock session returns None
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        # act & assert
        from project.services.user_service import get_user_by_username

        with pytest.raises(EntityNotFoundError) as exc_info:
            get_user_by_username(mock_session, "nonexistent")

        assert exc_info.value.entity_type == "User"


@pytest.mark.unit
@pytest.mark.level_3
class TestTokenCreationWithPatchedSettings:
    """Example: Patch get_settings to control configuration."""

    @patch("project.security.get_settings")
    def test_create_access_token_uses_settings(self, mock_get_settings):
        """Test that create_access_token uses settings for JWT encoding."""
        # arrange: mock settings
        mock_settings = Mock()
        mock_settings.SECRET_KEY = "test-secret"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 60
        mock_get_settings.return_value = mock_settings

        payload = TokenPayload(
            username="testuser",
            role="user",
            user_uuid=str(uuid4()),
        )

        # act
        token = create_access_token(payload)

        # assert
        assert token.access_token is not None
        assert token.token_type == "bearer"
        mock_get_settings.assert_called()

    @patch("project.security.get_settings")
    @patch("project.security.jwt.encode")
    def test_create_access_token_payload_structure(self, mock_encode, mock_get_settings):
        """Test that JWT payload contains expected fields."""
        # arrange
        mock_settings = Mock()
        mock_settings.SECRET_KEY = "test-secret"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_get_settings.return_value = mock_settings
        mock_encode.return_value = "mock-token"

        user_uuid = str(uuid4())
        payload = TokenPayload(
            username="john",
            role="admin",
            user_uuid=user_uuid,
        )

        # act
        create_access_token(payload)

        # assert: verify jwt.encode was called with correct structure
        mock_encode.assert_called_once()
        call_args = mock_encode.call_args[0][0]  # first positional arg

        assert call_args["username"] == "john"
        assert call_args["role"] == "admin"
        assert call_args["user_uuid"] == user_uuid
        assert "exp" in call_args


@pytest.mark.unit
@pytest.mark.level_3
class TestPasswordVerificationWithMock:
    """Example: Test password verification (uses real bcrypt, no mock needed)."""

    def test_verify_password_correct(self):
        """Test verify_password returns True for correct password."""
        from project.security import encrypt_password

        password = "mypassword"
        hashed = encrypt_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verify_password returns False for wrong password."""
        from project.security import encrypt_password

        hashed = encrypt_password("correctpassword")

        assert verify_password("wrongpassword", hashed) is False


@pytest.mark.unit
@pytest.mark.level_3
class TestTaskServiceWithMockedSession:
    """Example: Test task service with comprehensive mocking."""

    def test_get_tasks_with_pagination(self):
        """Test get_tasks applies pagination correctly."""
        # arrange
        mock_session = Mock()

        # create mock tasks
        mock_task1 = Mock(spec=Task)
        mock_task1.title = "Task 1"
        mock_task2 = Mock(spec=Task)
        mock_task2.title = "Task 2"

        # mock the query chain
        mock_scalars = Mock()
        mock_scalars.all.return_value = [mock_task1, mock_task2]
        mock_session.execute.return_value.scalars.return_value = mock_scalars

        pagination = PaginationParams(limit=10, offset=0)

        # act
        from project.services.task_service import get_tasks

        result = get_tasks(mock_session, pagination)

        # assert
        assert isinstance(result, PaginatedData)
        assert len(result.results) == 2
        assert result.limit == 10
        assert result.offset == 0


# =============================================================================
# EXERCISES - Complete these tests
# =============================================================================


@pytest.mark.unit
@pytest.mark.level_3
class TestAuthServiceWithMocks:
    """Exercise: Test auth service with mocked dependencies."""

    @patch("project.services.auth_service.get_user_by_username")
    @patch("project.services.auth_service.verify_password")
    def test_authenticate_user_success(self, mock_verify, mock_get_user):
        """TODO: Test authenticate_user returns user on valid credentials."""
        # arrange:
        # - mock_get_user should return a mock user
        # - mock_verify should return True
        #
        # act:
        # - call authenticate_user(session, "testuser", "password")
        #
        # assert:
        # - result should be the mock user
        # - mock_verify should have been called
        # YOUR CODE HERE
        pass

    @patch("project.services.auth_service.get_user_by_username")
    @patch("project.services.auth_service.verify_password")
    def test_authenticate_user_wrong_password(self, mock_verify, mock_get_user):
        """TODO: Test authenticate_user raises on wrong password."""
        # arrange:
        # - mock_get_user returns a user
        # - mock_verify returns False
        #
        # assert:
        # - AuthenticationError is raised
        # YOUR CODE HERE
        pass


@pytest.mark.unit
@pytest.mark.level_3
class TestDependenciesWithMocks:
    """Exercise: Test FastAPI dependencies with mocked services."""

    @patch("project.dependencies.decode_token")
    @patch("project.dependencies.get_user_by_username")
    def test_get_current_user_success(self, mock_get_user, mock_decode):
        """TODO: Test get_current_user returns user from valid token."""
        # arrange:
        # - mock_decode returns TokenData(username="testuser")
        # - mock_get_user returns a mock user
        #
        # act:
        # - call get_current_user(token="valid-token", session=mock_session)
        #
        # assert:
        # - returns the mock user
        # YOUR CODE HERE
        pass

    def test_require_admin_raises_for_non_admin(self, sample_user):
        """TODO: Test require_admin raises HTTPException for regular user."""
        # the sample_user fixture has role=USER
        # call require_admin(sample_user)
        # verify HTTPException with status 403 is raised
        #
        # hint: from fastapi import HTTPException
        # YOUR CODE HERE
        pass

    def test_require_admin_allows_admin(self, admin_user):
        """TODO: Test require_admin returns user for admin."""
        # the admin_user fixture has role=ADMIN
        # call require_admin(admin_user)
        # verify it returns the user without raising
        # YOUR CODE HERE
        pass


@pytest.mark.unit
@pytest.mark.level_3
class TestTokenExpirationWithPatchedDatetime:
    """Exercise: Test token expiration by patching datetime."""

    @patch("project.security.get_settings")
    @patch("project.security.datetime")
    def test_token_expiration_time(self, mock_datetime, mock_get_settings):
        """TODO: Test that token expiration is set correctly."""
        # arrange:
        # - set mock_datetime.now() to return a fixed time
        # - set mock_datetime.now(timezone.utc) to return same fixed time
        # - configure ACCESS_TOKEN_EXPIRE_MINUTES = 60
        #
        # act:
        # - create token
        #
        # assert:
        # - exp in the JWT payload should be now + 60 minutes
        #
        # hint: you may need to patch jwt.encode to capture the payload
        # YOUR CODE HERE
        pass


@pytest.mark.unit
@pytest.mark.level_3
class TestTaskServiceCreateWithMocks:
    """Exercise: Test task creation with mocked session."""

    def test_create_task_adds_to_session(self, sample_user):
        """TODO: Test create_task calls session.add() and commit()."""
        # arrange:
        # - create mock session with MagicMock()
        # - create TaskCreate with valid data
        #
        # act:
        # - call create_task(session, task_data, sample_user)
        #
        # assert:
        # - session.add was called once
        # - session.commit was called once
        # - session.refresh was called once
        # YOUR CODE HERE
        pass

    def test_create_task_raises_on_invalid_priority(self, sample_user):
        """TODO: Test create_task raises ValidationError for bad priority."""
        # note: this tests the SERVICE validation, not Pydantic
        # the service has its own priority check
        # you may need to bypass Pydantic validation to test this
        #
        # hint: create a Mock TaskCreate object instead of real TaskCreate
        # YOUR CODE HERE
        pass
