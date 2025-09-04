import pytest
from fastapi.testclient import TestClient
from backend.api.app import app

client = TestClient(app)

@pytest.mark.skip(reason="Auth middleware not implemented")
def test_auth_middleware_missing_token():
    response = client.get("/api/tasks")
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}

@pytest.mark.skip(reason="Auth middleware not implemented")
def test_auth_middleware_invalid_token():
    response = client.get("/api/tasks", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid authentication credentials"}
