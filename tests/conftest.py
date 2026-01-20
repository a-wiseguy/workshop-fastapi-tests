"""Test configuration and fixtures for pytest unit testing workshop."""

import os
from collections.abc import Generator
from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from project.config import Settings
from project.db.models.base import Base
from project.db.models.task import Task, TaskStatus
from project.db.models.user import Role, User
from project.security import encrypt_password

# =============================================================================
# UNIT TEST FIXTURES (no database, mocks only)
# =============================================================================


@pytest.fixture
def test_settings() -> Settings:
    """Provide test settings without loading from .env."""
    return Settings(
        DEBUG=True,
        SECRET_KEY="test-secret-key-for-testing",
        DB_TYPE="sqlite",
        DB_URL="sqlite:///:memory:",
        SQLALCHEMY_ECHO=False,
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
    )


@pytest.fixture
def sample_user() -> Mock:
    """Create a sample user mock for testing (not persisted to DB)."""
    user = Mock(spec=User)
    user.uuid = uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.password_hash = "$2b$12$test_hash_placeholder"
    user.role = Role.USER.value
    user.created_at = datetime.now()
    return user


@pytest.fixture
def admin_user() -> Mock:
    """Create an admin user mock for testing (not persisted to DB)."""
    user = Mock(spec=User)
    user.uuid = uuid4()
    user.username = "admin"
    user.email = "admin@example.com"
    user.password_hash = "$2b$12$admin_hash_placeholder"
    user.role = Role.ADMIN.value
    user.created_at = datetime.now()
    return user


@pytest.fixture
def sample_task(sample_user: Mock) -> Mock:
    """Create a sample task mock for testing (not persisted to DB)."""
    task = Mock(spec=Task)
    task.uuid = uuid4()
    task.title = "Test Task"
    task.description = "A test task description"
    task.status = TaskStatus.TODO.value
    task.priority = 3
    task.due_date = None
    task.created_by = sample_user.uuid
    task.assigned_to = None
    task.created_at = datetime.now()
    return task


# =============================================================================
# INTEGRATION TEST FIXTURES (real SQLite database)
# =============================================================================


def get_worker_id() -> str:
    """Get xdist worker id for parallel test isolation."""
    return os.environ.get("PYTEST_XDIST_WORKER", "master")


def create_test_engine() -> Engine:
    """Create a fresh SQLite test database engine."""
    worker_id = get_worker_id()
    db_file = f"test_{worker_id}_{uuid4().hex}.sqlite"

    engine = create_engine(
        f"sqlite:///{db_file}",
        echo=False,
        connect_args={"check_same_thread": False},
    )

    return engine


def setup_test_database(engine: Engine) -> None:
    """Create all tables in the test database."""
    Base.metadata.create_all(bind=engine)


def teardown_test_database(engine: Engine) -> None:
    """Drop all tables and cleanup the test database file."""
    engine.dispose()

    db_url = str(engine.url)
    if db_url.startswith("sqlite:///") and db_url != "sqlite:///:memory:":
        db_file = db_url[10:]
        for suffix in ["", "-journal", "-wal", "-shm"]:
            file_path = db_file + suffix
            if os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except Exception:
                    pass


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """
    Database session fixture for integration tests.

    Creates a fresh SQLite database for each test, with all tables.
    Auto-tears down after the test completes.

    Usage:
        def test_something(db_session: Session):
            # db_session is a real SQLAlchemy session
            user = User(username="test", ...)
            db_session.add(user)
            db_session.commit()
    """
    engine = create_test_engine()
    setup_test_database(engine)

    with Session(engine) as session:
        yield session
        session.rollback()

    teardown_test_database(engine)


@pytest.fixture
def created_user(db_session: Session) -> User:
    """Create and persist a test user in the database."""
    user = User(
        uuid=uuid4(),
        username="testuser",
        email="testuser@example.com",
        password_hash=encrypt_password("testpass123"),
        role=Role.USER.value,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def created_admin(db_session: Session) -> User:
    """Create and persist an admin user in the database."""
    admin = User(
        uuid=uuid4(),
        username="admin",
        email="admin@example.com",
        password_hash=encrypt_password("adminpass123"),
        role=Role.ADMIN.value,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def created_task(db_session: Session, created_user: User) -> Task:
    """Create and persist a test task in the database."""
    task = Task(
        uuid=uuid4(),
        title="Test Task",
        description="A test task for integration tests",
        status=TaskStatus.TODO.value,
        priority=3,
        created_by=created_user.uuid,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task
