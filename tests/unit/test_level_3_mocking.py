"""
Level 3: Mocking and Patching
==============================
Goal: Isolate code under test by replacing dependencies with mocks.

Focus: 5 practical mocking patterns for FastAPI service/dependency testing.

Run these tests:
    pytest tests/unit/test_level_3_mocking.py -v
    pytest -k level_3 -v
"""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from project.db.models.task import Task
from project.db.models.user import Role, User
from project.exceptions import AuthenticationError, EntityNotFoundError
from project.security import TokenData, TokenPayload


@pytest.mark.unit
@pytest.mark.level_3
class TestLevel3:
    """
    Level 3: Mocking and Patching

    These 5 tests cover essential mocking patterns for FastAPI apps:
    1. Mock DB session to test services without database
    2. Service raises exception when entity not found
    3. Patch settings/config to control test environment
    4. Mock token decode in auth dependency
    5. Test role-based access control (require_admin)
    """

    # =========================================================================
    # TEST 1: Mock DB Session for Service Testing
    # WHY: Test service logic without needing a real database
    # =========================================================================
    def test_service_with_mocked_session(self):
        """Test service function using mocked SQLAlchemy session.

        Real-world: You want to test your service logic (query building,
        result processing) without spinning up a test database.
        """
        from project.services.user_service import get_user_by_username

        # arrange: create mock session and user
        mock_session = Mock()
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"

        # configure mock to return user when queried
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_user

        # act: call service with mock session
        result = get_user_by_username(mock_session, "testuser")

        # assert: service returns expected result
        assert result.username == "testuser"
        assert result.email == "test@example.com"

        # verify session was actually used
        mock_session.execute.assert_called_once()

    # =========================================================================
    # TEST 2: Service Raises Exception When Not Found
    # WHY: Services must raise domain exceptions, not return None
    # =========================================================================
    def test_service_raises_when_entity_not_found(self):
        """Test that service raises EntityNotFoundError when lookup fails.

        Real-world: When session.scalar_one_or_none() returns None,
        your service should raise EntityNotFoundError, not return None.
        """
        from project.services.user_service import get_user_by_username

        # arrange: mock session returns None (user not found)
        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        # act & assert: service raises EntityNotFoundError
        with pytest.raises(EntityNotFoundError) as exc_info:
            get_user_by_username(mock_session, "nonexistent")

        assert exc_info.value.entity_type == "User"
        assert exc_info.value.identifier == "nonexistent"

    # =========================================================================
    # TEST 3: Patch Settings to Control Test Environment
    # WHY: Test config-dependent code without modifying .env
    # =========================================================================
    @patch("project.security.get_settings")
    def test_token_creation_with_patched_settings(self, mock_get_settings):
        """Test token creation using patched settings.

        Real-world: Test that your auth code correctly uses settings
        like SECRET_KEY and ALGORITHM without requiring .env file.
        """
        from project.security import create_access_token

        # arrange: mock settings
        mock_settings = Mock()
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_get_settings.return_value = mock_settings

        payload = TokenPayload(
            username="testuser",
            role="user",
            user_uuid=str(uuid4()),
        )

        # act: create token
        token = create_access_token(payload)

        # assert: token was created with patched settings
        assert token.access_token is not None
        assert token.token_type == "bearer"
        mock_get_settings.assert_called()

    # =========================================================================
    # TEST 4: Mock Token Decode in Auth Dependency
    # WHY: Test auth dependency without creating real JWT tokens
    # =========================================================================
    @patch("project.dependencies.decode_token")
    @patch("project.dependencies.get_user_by_username")
    def test_get_current_user_dependency(self, mock_get_user, mock_decode):
        """Test get_current_user dependency with mocked token decode.

        Real-world: Test that your auth dependency correctly:
        - Decodes the JWT token
        - Looks up the user from decoded username
        - Returns the user object
        """
        from project.dependencies import get_current_user

        # arrange: mock token decode and user lookup
        mock_decode.return_value = TokenData(username="testuser")
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_get_user.return_value = mock_user
        mock_session = Mock()

        # act: call dependency
        result = get_current_user(token="fake-token", session=mock_session)

        # assert: returns user from decoded token
        assert result.username == "testuser"
        mock_decode.assert_called_once_with("fake-token")
        mock_get_user.assert_called_once_with(mock_session, "testuser")

    # =========================================================================
    # TEST 5: Test Role-Based Access Control
    # WHY: Ensure admin-only endpoints reject non-admin users
    # =========================================================================
    def test_require_admin_access_control(self, sample_user, admin_user):
        """Test require_admin dependency enforces admin role.

        Real-world: Admin-only endpoints must reject regular users
        with HTTP 403, but allow admin users through.
        """
        from project.dependencies import require_admin

        # non-admin user should be rejected
        with pytest.raises(HTTPException) as exc_info:
            require_admin(sample_user)

        assert exc_info.value.status_code == 403
        assert "Admin" in exc_info.value.detail

        # admin user should pass through
        result = require_admin(admin_user)
        assert result.role == Role.ADMIN.value


# =============================================================================
# EXERCISES - Practice mocking patterns
# =============================================================================


@pytest.mark.unit
@pytest.mark.level_3
class TestLevel3Exercises:
    """
    Exercises: Apply what you learned above.

    Complete these tests following the same patterns.
    """

    def test_task_service_with_mocked_session(self):
        """Exercise: Test get_task_by_uuid with mocked session.

        - Create mock session
        - Configure it to return a mock task
        - Call get_task_by_uuid(session, some_uuid)
        - Verify it returns the mock task
        """
        from project.services.task_service import get_task_by_uuid

        # arrange: create mock session and user
        mock_session = Mock()
        mock_task = Mock(spec=Task)
        mock_task.title = "Test Task"
        mock_task.description = "Deze Task is een test"

        # configure mock to return user when queried
        mock_session.execute.return_value.scalar_one_or_none.return_value = mock_task

        # act: call service with mock session
        result = get_task_by_uuid(mock_session, mock_task.uuid)

        # assert: service returns expected result
        assert result.title == "Test Task"
        assert result.description == "Deze Task is een test"

        # verify session was actually used
        mock_session.execute.assert_called_once()

    def test_task_service_raises_not_found(self):
        """Exercise: Test get_task_by_uuid raises EntityNotFoundError.

        - Create mock session returning None
        - Call get_task_by_uuid
        - Verify EntityNotFoundError is raised with entity_type="Task"
        """
        from project.services.task_service import get_task_by_uuid

        mock_session = Mock()
        mock_session.execute.return_value.scalar_one_or_none.return_value = None

        # act & assert: service raises EntityNotFoundError
        with pytest.raises(EntityNotFoundError) as exc_info:
            get_task_by_uuid(mock_session, "no task")

        assert exc_info.value.entity_type == "Task"
        assert exc_info.value.identifier == "no task"

    @patch("project.services.auth_service.get_user_by_username")
    @patch("project.services.auth_service.verify_password")
    def test_authenticate_user_with_mocks(self, mock_verify, mock_get_user):
        """Exercise: Test authenticate_user with mocked dependencies.

        - mock_get_user returns a mock user
        - mock_verify returns True (password matches)
        - Call authenticate_user(session, "user", "pass")
        - Verify it returns the mock user

        Then test the failure case:
        - mock_verify returns False
        - Verify AuthenticationError is raised
        """
        from project.services.auth_service import authenticate_user

        # arrange: create mock session and user
        mock_session = Mock()
        mock_user = Mock(spec=User)
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"

        # configure mock to return user when queried
        mock_get_user.return_value = mock_user
        mock_verify.return_value = True

        authenticated_user = authenticate_user(mock_session, "testuser", "pass")

        assert authenticated_user == mock_user

        mock_verify.return_value = False

        with pytest.raises(AuthenticationError) as exc_info:
            authenticate_user(mock_session, "testuser", "wrongpassword")
