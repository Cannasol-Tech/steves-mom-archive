import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker, Session

from backend.api.app import app
from backend.database import get_db
from backend.models.orm.task import Base
from backend.models.orm.task import Task as ORMTask
from backend.models.task_models import Task, TaskStatus

SQLALCHEMY_DATABASE_URL = "sqlite://"

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield SessionLocal()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="client")
def client_fixture(session):
    def get_db_override():
        return session

    app.dependency_overrides[get_db] = get_db_override
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_task(session: Session):
    """Create a task in the DB for testing and clean it up afterward."""
    db_task = ORMTask(
        id=uuid.uuid4(),
        title="Test Task for Approval",
        description="A task to be approved or rejected.",
        status=TaskStatus.PENDING_APPROVAL
    )
    session.add(db_task)
    session.commit()
    session.refresh(db_task)
    
    yield db_task
    
    session.delete(db_task)
    session.commit()

def test_approve_task_api(client, mock_task):
    """Test approving a task via the API."""
    response = client.post(f"/api/tasks/{mock_task.id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"

def test_reject_task_api(client, mock_task):
    """Test rejecting a task via the API."""
    response = client.post(f"/api/tasks/{mock_task.id}/reject")
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"

def test_approve_nonexistent_task(client):
    """Test approving a task that does not exist."""
    non_existent_uuid = uuid.uuid4()
    response = client.post(f"/api/tasks/{non_existent_uuid}/approve")
    assert response.status_code == 404

def test_invalid_approval_transition_api(client, mock_task):
    """Test an invalid state transition via the API."""
    # First, approve the task
    client.post(f"/api/tasks/{mock_task.id}/approve")
    
    # Now, try to reject it (which should fail)
    response = client.post(f"/api/tasks/{mock_task.id}/reject")
    assert response.status_code == 409  # Conflict
