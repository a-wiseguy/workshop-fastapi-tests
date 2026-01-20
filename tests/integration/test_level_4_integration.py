"""
Level 4: Integration Tests
===========================
Goal: Test service logic with a real database.

Integration tests verify that multiple components work together correctly:
- Service functions execute real database queries
- ORM relationships load properly
- Complex filtering and pagination work
- Data integrity is maintained

Key differences from unit tests:
- Uses real SQLite database (created fresh per test)
- No mocking of database session
- Tests actual query execution
- Slower than unit tests, but higher confidence

Run these tests:
    pytest tests/integration/ -v
    pytest -k level_4 -v
"""

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from project.db.models.task import Task, TaskStatus
from project.db.models.user import Role, User
from project.exceptions import EntityNotFoundError
from project.security import encrypt_password
from project.services import task_service, user_service
from project.utils.pagination import PaginationParams


@pytest.mark.integration
@pytest.mark.level_4
class TestLevel4:
    """
    Level 4: Integration Tests

    These 5 tests demonstrate essential integration testing patterns:
    1. Service with database - query execution and ORM mapping
    2. Pagination with real data - offset, limit, total count
    3. Filtering across relationships - joins and foreign keys
    4. Error handling with database - EntityNotFoundError
    5. Data integrity - create, update, verify state
    """

    # =========================================================================
    # TEST 1: Service Query Execution
    # WHY: Verify service queries actually work against a real database
    # =========================================================================
    def test_user_service_creates_and_retrieves_user(self, db_session: Session):
        """Test user creation and retrieval through service layer.

        Real-world: This tests the full flow from service → ORM → database → ORM.
        Unlike unit tests, this catches SQL syntax errors and ORM mapping issues.
        """
        from project.db.models.user import UserCreate

        # arrange: create admin for audit fields
        admin = User(
            uuid=uuid4(),
            username="admin",
            email="admin@test.com",
            password_hash=encrypt_password("admin123"),
            role=Role.ADMIN.value,
        )
        db_session.add(admin)
        db_session.commit()

        # act: create user through service
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            password="password123",
            role=Role.USER,
        )
        created = user_service.create_user(db_session, user_data)

        # assert: user is in database with correct data
        assert created.uuid is not None
        assert created.username == "newuser"
        assert created.email == "newuser@example.com"
        assert created.role == Role.USER.value

        # verify it can be retrieved
        retrieved = user_service.get_user_by_uuid(db_session, created.uuid)
        assert retrieved.uuid == created.uuid
        assert retrieved.username == "newuser"

    # =========================================================================
    # TEST 2: Pagination with Real Data
    # WHY: Pagination bugs often only appear with real database queries
    # =========================================================================
    def test_task_pagination_with_real_database(self, db_session: Session, created_user: User):
        """Test pagination returns correct subsets of data.

        Real-world: Pagination logic can have off-by-one errors, wrong totals,
        or ordering issues that only appear with real database queries.
        """
        # arrange: create 15 tasks
        for i in range(15):
            task = Task(
                uuid=uuid4(),
                title=f"Task {i:02d}",
                description=f"Description for task {i}",
                status=TaskStatus.TODO.value,
                priority=(i % 5) + 1,
                created_by=created_user.uuid,
            )
            db_session.add(task)
        db_session.commit()

        # act: get first page
        page1_params = PaginationParams(limit=5, offset=0, sort_order="asc")
        page1 = task_service.get_tasks(db_session, page1_params)

        # assert: first page has correct data
        assert page1.total == 15
        assert page1.limit == 5
        assert page1.offset == 0
        assert len(page1.results) == 5

        # act: get second page
        page2_params = PaginationParams(limit=5, offset=5, sort_order="asc")
        page2 = task_service.get_tasks(db_session, page2_params)

        # assert: second page has different data
        assert page2.total == 15
        assert page2.offset == 5
        assert len(page2.results) == 5

        # pages should not overlap
        page1_uuids = {t.uuid for t in page1.results}
        page2_uuids = {t.uuid for t in page2.results}
        assert page1_uuids.isdisjoint(page2_uuids)

        # act: get last partial page
        page3_params = PaginationParams(limit=5, offset=10, sort_order="asc")
        page3 = task_service.get_tasks(db_session, page3_params)

        assert len(page3.results) == 5  # last 5 tasks

    # =========================================================================
    # TEST 3: Filtering Across Relationships
    # WHY: Complex queries with JOINs can fail in subtle ways
    # =========================================================================
    def test_task_filtering_by_status_and_assignment(self, db_session: Session):
        """Test filtering tasks by status and assigned user.

        Real-world: Filtering logic with foreign keys needs to work correctly
        when the FK is NULL vs when it points to a specific user.
        """
        # arrange: create two users
        user1 = User(
            uuid=uuid4(),
            username="user1",
            email="user1@test.com",
            password_hash=encrypt_password("pass1"),
            role=Role.USER.value,
        )
        user2 = User(
            uuid=uuid4(),
            username="user2",
            email="user2@test.com",
            password_hash=encrypt_password("pass2"),
            role=Role.USER.value,
        )
        db_session.add_all([user1, user2])
        db_session.commit()

        # create tasks with different statuses and assignments
        tasks_data = [
            ("Task A", TaskStatus.TODO, user1.uuid, user1.uuid),      # todo, assigned to user1
            ("Task B", TaskStatus.TODO, user1.uuid, user2.uuid),      # todo, assigned to user2
            ("Task C", TaskStatus.IN_PROGRESS, user1.uuid, user1.uuid),  # in_progress, assigned to user1
            ("Task D", TaskStatus.DONE, user1.uuid, None),            # done, unassigned
            ("Task E", TaskStatus.TODO, user1.uuid, None),            # todo, unassigned
        ]

        for title, status, created_by, assigned_to in tasks_data:
            task = Task(
                uuid=uuid4(),
                title=title,
                status=status.value,
                priority=3,
                created_by=created_by,
                assigned_to=assigned_to,
            )
            db_session.add(task)
        db_session.commit()

        # act: filter by status=TODO
        pagination = PaginationParams(limit=10, offset=0)
        todo_tasks = task_service.get_tasks(
            db_session, pagination, status_filter=TaskStatus.TODO
        )

        # assert: only TODO tasks returned
        assert todo_tasks.total == 3  # Task A, B, E
        for task in todo_tasks.results:
            assert task.status == TaskStatus.TODO.value

        # act: filter by assigned_to=user1
        user1_tasks = task_service.get_tasks(
            db_session, pagination, assigned_to=user1.uuid
        )

        # assert: only user1's tasks
        assert user1_tasks.total == 2  # Task A, C
        for task in user1_tasks.results:
            assert task.assigned_to == user1.uuid

        # act: combine filters
        user1_todo = task_service.get_tasks(
            db_session, pagination,
            status_filter=TaskStatus.TODO,
            assigned_to=user1.uuid,
        )

        # assert: only TODO tasks assigned to user1
        assert user1_todo.total == 1  # Only Task A

    # =========================================================================
    # TEST 4: Error Handling with Database
    # WHY: Verify exceptions are raised correctly when data doesn't exist
    # =========================================================================
    def test_service_raises_not_found_for_missing_entity(self, db_session: Session):
        """Test that services raise EntityNotFoundError for non-existent data.

        Real-world: When a UUID doesn't exist in the database, the service
        must raise a proper exception that routers can convert to HTTP 404.
        """
        non_existent_uuid = uuid4()

        # user not found
        with pytest.raises(EntityNotFoundError) as exc_info:
            user_service.get_user_by_uuid(db_session, non_existent_uuid)

        assert exc_info.value.entity_type == "User"
        assert str(non_existent_uuid) in exc_info.value.identifier

        # task not found
        with pytest.raises(EntityNotFoundError) as exc_info:
            task_service.get_task_by_uuid(db_session, non_existent_uuid)

        assert exc_info.value.entity_type == "Task"

    # =========================================================================
    # TEST 5: Data Integrity Through Operations
    # WHY: Verify create/update/delete maintain consistent state
    # =========================================================================
    def test_task_lifecycle_maintains_integrity(self, db_session: Session, created_user: User):
        """Test task create/update/delete maintains database integrity.

        Real-world: CRUD operations must leave the database in a consistent state.
        This test verifies the full lifecycle of an entity.
        """
        from project.db.models.task import TaskCreate, TaskUpdate

        # CREATE
        task_data = TaskCreate(
            title="Lifecycle Test Task",
            description="Testing full lifecycle",
            status=TaskStatus.TODO,
            priority=2,
        )
        created = task_service.create_task(db_session, task_data, created_user)

        assert created.uuid is not None
        assert created.title == "Lifecycle Test Task"
        assert created.status == TaskStatus.TODO.value

        # verify in database
        db_task = db_session.get(Task, created.uuid)
        assert db_task is not None
        assert db_task.title == "Lifecycle Test Task"

        # UPDATE
        update_data = TaskUpdate(
            status=TaskStatus.IN_PROGRESS,
            priority=5,
        )
        updated = task_service.update_task(db_session, created.uuid, update_data)

        assert updated.status == TaskStatus.IN_PROGRESS.value
        assert updated.priority == 5
        assert updated.title == "Lifecycle Test Task"  # unchanged

        # verify update persisted
        db_session.expire(db_task)
        db_task = db_session.get(Task, created.uuid)
        assert db_task.status == TaskStatus.IN_PROGRESS.value

        # DELETE
        task_service.delete_task(db_session, created.uuid)

        # verify deleted
        db_task = db_session.get(Task, created.uuid)
        assert db_task is None

        # verify raises not found after delete
        with pytest.raises(EntityNotFoundError):
            task_service.get_task_by_uuid(db_session, created.uuid)


# =============================================================================
# EXERCISES - Practice integration testing patterns
# =============================================================================


@pytest.mark.integration
@pytest.mark.level_4
class TestLevel4Exercises:
    """
    Exercises: Apply integration testing patterns.

    Complete these tests following the same patterns.
    """

    def test_get_users_returns_all_active_users(self, db_session: Session):
        """Exercise: Test user listing with active filter.

        - Create 3 users (one should be manually set as archived if you add that field)
        - Call get_all_users(db_session)
        - Verify all created users are returned
        """
        # YOUR CODE HERE
        pass

    def test_task_update_preserves_unset_fields(self, db_session: Session, created_task: Task):
        """Exercise: Test partial update doesn't overwrite unset fields.

        - created_task fixture provides a task with title and description
        - Update only the status using TaskUpdate(status=TaskStatus.DONE)
        - Verify title and description are unchanged
        """
        # YOUR CODE HERE
        pass

    def test_pagination_empty_results(self, db_session: Session):
        """Exercise: Test pagination with offset beyond available data.

        - Create 3 tasks
        - Request page with offset=100, limit=10
        - Verify total is 3 but results list is empty
        """
        # YOUR CODE HERE
        pass
