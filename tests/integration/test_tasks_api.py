import pytest
import uuid
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from types import SimpleNamespace
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker

from backend.api.app import app
from backend.database import get_db
from backend.models.orm.task import Base, Task as ORMTask
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



def test_create_task(client, session):
    task_data = Task(title="Test Task", description="Test Description")
    response = client.post("/api/tasks/", content=task_data.model_dump_json())
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Description"
    assert "id" in data

def test_read_task(client, session):
    response = client.post("/api/tasks/", json={"title": "Test Task", "description": "Test Description"})
    task_id = response.json()["id"]

    response = client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["id"] == task_id

def test_read_tasks(client, session):
    client.post("/api/tasks/", json={"title": "Test Task 1", "description": "Test Description 1"})
    client.post("/api/tasks/", json={"title": "Test Task 2", "description": "Test Description 2"})

    response = client.get("/api/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

def test_update_task(client, session, monkeypatch):
    response = client.post("/api/tasks/", json={"title": "Test Task", "description": "Test Description"})
    task_id = response.json()["id"]

    # Patch broadcast to capture calls
    sent = []

    class FakeManager:
        async def broadcast(self, message: str):
            sent.append(message)

    import backend.api.routes.tasks as tasks_module
    monkeypatch.setattr(tasks_module, "manager", FakeManager())

    response = client.put(f"/api/tasks/{task_id}", json={"title": "Updated Task"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Task"
    # Ensure a broadcast occurred
    assert len(sent) == 1

def test_delete_task(client, session):
    response = client.post("/api/tasks/", json={"title": "Test Task", "description": "Test Description"})
    task_id = response.json()["id"]

    response = client.delete(f"/api/tasks/{task_id}")
    assert response.status_code == 204

    response = client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 404

def test_read_task_not_found(client, session):
    response = client.get(f"/api/tasks/{uuid.uuid4()}")
    assert response.status_code == 404

def test_read_tasks_with_date_filter(client, session):
    now = datetime.now(timezone.utc)
    task1 = ORMTask(title="Task 1", created_at=now - timedelta(days=2))
    task2 = ORMTask(title="Task 2", created_at=now - timedelta(days=1))
    task3 = ORMTask(title="Task 3", created_at=now)
    session.add_all([task1, task2, task3])
    session.commit()

    def rfc3339(dt):
        return dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

    # Filter by start_date
    response = client.get(f"/api/tasks/?start_date={rfc3339(now - timedelta(days=1))}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {d['title'] for d in data} == {"Task 2", "Task 3"}

    # Filter by end_date
    response = client.get(f"/api/tasks/?end_date={rfc3339(now - timedelta(days=1) + timedelta(seconds=1))}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {d['title'] for d in data} == {"Task 1", "Task 2"}

    # Filter by start_date and end_date
    response = client.get(f"/api/tasks/?start_date={rfc3339(now - timedelta(days=1.5))}&end_date={rfc3339(now - timedelta(days=0.5))}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['title'] == "Task 2"

def test_read_tasks_with_search_filter(client, session):
    task1 = ORMTask(title="Important Task", description="A very important task.")
    task2 = ORMTask(title="Another Task", description="Some details here.")
    task3 = ORMTask(title="Final Review", description="Review this important document.")
    session.add_all([task1, task2, task3])
    session.commit()

    # Search in title
    response = client.get("/api/tasks/?search=important")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {d['title'] for d in data} == {"Important Task", "Final Review"}

    # Search in description
    response = client.get("/api/tasks/?search=details")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['title'] == "Another Task"

    # Search with no results
    response = client.get("/api/tasks/?search=nonexistent")
    assert response.status_code == 200
    assert len(response.json()) == 0

def test_read_tasks_with_pagination_and_filters(client, session):
    for i in range(10):
        session.add(ORMTask(title=f"Task {i}", status=TaskStatus.PENDING))
    session.commit()

    # Test pagination with a status filter
    response = client.get("/api/tasks/?status=pending&skip=2&limit=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["title"] == "Task 2"
    assert data[2]["title"] == "Task 4"

def test_read_tasks_with_status_filter(client, session):
    session.add(ORMTask(title="Pending Task", status=TaskStatus.PENDING))
    session.add(ORMTask(title="Completed Task", status=TaskStatus.COMPLETED))
    session.commit()

    # Filter by PENDING
    response = client.get("/api/tasks/?status=pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Pending Task"
    assert data[0]["status"] == "pending"

    # Filter by COMPLETED
    response = client.get("/api/tasks/?status=completed")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Completed Task"
    assert data[0]["status"] == "completed"

    # Filter by a status with no tasks
    response = client.get("/api/tasks/?status=in_progress")
    assert response.status_code == 200
    assert len(response.json()) == 0
