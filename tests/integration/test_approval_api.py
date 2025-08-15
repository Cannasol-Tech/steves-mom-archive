import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.api.app import app
from backend.database import get_db
from backend.models import orm, task_models

client = TestClient(app)

# This is a simplified version of the dependency override from test_tasks_api.py
# In a real app, you'd share this test setup.
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

orm.Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db_session():
    """Yield a new database session for each test function."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def mock_task(db_session: Session):
    """Create a task in the DB for testing and clean it up afterward."""
    task_data = task_models.TaskCreate(
        title="Test Task for Approval",
        description="A task to be approved or rejected.",
        status=task_models.TaskStatus.PENDING_APPROVAL
    )
    db_task = orm.task.Task(**task_data.model_dump(), id=uuid.uuid4())
    db_session.add(db_task)
    db_session.commit()
    db_session.refresh(db_task)
    
    yield db_task
    
    db_session.delete(db_task)
    db_session.commit()

def test_approve_task_api(mock_task):
    """Test approving a task via the API."""
    response = client.post(f"/tasks/{mock_task.id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

def test_reject_task_api(mock_task):
    """Test rejecting a task via the API."""
    response = client.post(f"/tasks/{mock_task.id}/reject")
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"

def test_approve_nonexistent_task():
    """Test approving a task that does not exist."""
    non_existent_uuid = uuid.uuid4()
    response = client.post(f"/tasks/{non_existent_uuid}/approve")
    assert response.status_code == 404

def test_invalid_approval_transition_api(mock_task):
    """Test an invalid state transition via the API."""
    # First, approve the task
    client.post(f"/tasks/{mock_task.id}/approve")
    
    # Now, try to reject it (which should fail)
    response = client.post(f"/tasks/{mock_task.id}/reject")
    assert response.status_code == 409  # Conflict
