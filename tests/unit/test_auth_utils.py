"""
Unit tests for backend.functions.auth_utils

Tests authentication utilities for Azure Functions including:
- UserPrincipal class functionality
- Authentication header parsing
- Role-based authorization
- Authentication decorators
- Error handling and edge cases

Author: Cannasol Technologies
Date: 2025-01-04
Version: 1.0.0
"""

import base64
import json
import pytest
from unittest.mock import Mock, patch
import asyncio

import sys
from pathlib import Path

# Ensure backend package is importable
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.functions.auth_utils import (
    UserPrincipal,
    get_user_principal,
    require_auth,
    require_roles,
    require_all_roles,
    create_auth_response,
    log_auth_event,
    auth_decorator,
    require_admin,
    require_user,
    allow_anonymous
)


class TestUserPrincipal:
    """Test UserPrincipal class functionality."""

    def test_user_principal_creation(self):
        """Test creating UserPrincipal with valid data."""
        data = {
            "userId": "user123",
            "userDetails": "john.doe@example.com",
            "userRoles": ["user", "admin"],
            "identityProvider": "aad"
        }

        user = UserPrincipal(data)
        assert user.user_id == "user123"
        assert user.user_details == "john.doe@example.com"
        assert user.user_roles == ["user", "admin"]
        assert user.identity_provider == "aad"

    def test_user_principal_with_missing_fields(self):
        """Test UserPrincipal with missing optional fields."""
        data = {}

        user = UserPrincipal(data)
        assert user.user_id == ""
        assert user.user_details == ""
        assert user.user_roles == []
        assert user.identity_provider == ""

    def test_has_role(self):
        """Test has_role method."""
        data = {
            "userRoles": ["user", "admin", "moderator"]
        }
        user = UserPrincipal(data)

        assert user.has_role("user") is True
        assert user.has_role("admin") is True
        assert user.has_role("moderator") is True
        assert user.has_role("guest") is False
        assert user.has_role("superuser") is False

    def test_has_any_role(self):
        """Test has_any_role method."""
        data = {
            "userRoles": ["user", "moderator"]
        }
        user = UserPrincipal(data)

        # Should return True if user has any of the specified roles
        assert user.has_any_role(["admin", "user"]) is True
        assert user.has_any_role(["moderator", "guest"]) is True
        assert user.has_any_role(["user"]) is True

        # Should return False if user has none of the specified roles
        assert user.has_any_role(["admin", "guest"]) is False
        assert user.has_any_role(["superuser"]) is False
        assert user.has_any_role([]) is False

    def test_has_all_roles(self):
        """Test has_all_roles method."""
        data = {
            "userRoles": ["user", "admin", "moderator"]
        }
        user = UserPrincipal(data)

        # Should return True if user has all specified roles
        assert user.has_all_roles(["user"]) is True
        assert user.has_all_roles(["user", "admin"]) is True
        assert user.has_all_roles(["user", "admin", "moderator"]) is True

        # Should return False if user is missing any specified role
        assert user.has_all_roles(["user", "admin", "guest"]) is False
        assert user.has_all_roles(["superuser"]) is False
        assert user.has_all_roles([]) is True  # Empty list should return True

    def test_to_dict(self):
        """Test to_dict serialization method."""
        data = {
            "userId": "user123",
            "userDetails": "john.doe@example.com",
            "userRoles": ["user", "admin"],
            "identityProvider": "aad"
        }

        user = UserPrincipal(data)
        result = user.to_dict()

        assert result == data
        assert isinstance(result, dict)


class TestGetUserPrincipal:
    """Test get_user_principal function."""

    def test_get_user_principal_valid_header(self):
        """Test extracting user principal from valid header."""
        user_data = {
            "userId": "user123",
            "userDetails": "john.doe@example.com",
            "userRoles": ["user"],
            "identityProvider": "aad"
        }

        # Encode the user data as base64 JSON
        json_str = json.dumps(user_data)
        encoded = base64.b64encode(json_str.encode()).decode()

        # Mock request with header
        mock_request = Mock()
        mock_request.headers = {"x-ms-client-principal": encoded}

        user = get_user_principal(mock_request)

        assert user is not None
        assert user.user_id == "user123"
        assert user.user_details == "john.doe@example.com"
        assert user.user_roles == ["user"]
        assert user.identity_provider == "aad"

    def test_get_user_principal_no_header(self):
        """Test when no authentication header is present."""
        mock_request = Mock()
        mock_request.headers = {}

        user = get_user_principal(mock_request)
        assert user is None

    def test_get_user_principal_invalid_base64(self):
        """Test with invalid base64 encoding."""
        mock_request = Mock()
        mock_request.headers = {"x-ms-client-principal": "invalid-base64!@#"}

        user = get_user_principal(mock_request)
        assert user is None

    def test_get_user_principal_invalid_json(self):
        """Test with valid base64 but invalid JSON."""
        invalid_json = "not valid json"
        encoded = base64.b64encode(invalid_json.encode()).decode()

        mock_request = Mock()
        mock_request.headers = {"x-ms-client-principal": encoded}

        user = get_user_principal(mock_request)
        assert user is None

    def test_get_user_principal_exception_handling(self):
        """Test exception handling in get_user_principal."""
        mock_request = Mock()
        mock_request.headers.get.side_effect = Exception("Test exception")

        user = get_user_principal(mock_request)
        assert user is None


class TestRequireAuth:
    """Test require_auth function."""

    def test_require_auth_with_valid_user(self):
        """Test require_auth with authenticated user."""
        user_data = {
            "userId": "user123",
            "userDetails": "john.doe@example.com",
            "userRoles": ["user"],
            "identityProvider": "aad"
        }

        json_str = json.dumps(user_data)
        encoded = base64.b64encode(json_str.encode()).decode()

        mock_request = Mock()
        mock_request.headers = {"x-ms-client-principal": encoded}

        user = require_auth(mock_request)
        assert user is not None
        assert user.user_id == "user123"

    def test_require_auth_without_user(self):
        """Test require_auth raises ValueError when no user."""
        mock_request = Mock()
        mock_request.headers = {}

        with pytest.raises(ValueError, match="Authentication required"):
            require_auth(mock_request)


class TestRequireRoles:
    """Test require_roles function."""

    def test_require_roles_with_valid_role(self):
        """Test require_roles with user having required role."""
        user_data = {
            "userId": "user123",
            "userDetails": "john.doe@example.com",
            "userRoles": ["user", "admin"],
            "identityProvider": "aad"
        }

        json_str = json.dumps(user_data)
        encoded = base64.b64encode(json_str.encode()).decode()

        mock_request = Mock()
        mock_request.headers = {"x-ms-client-principal": encoded}

        user = require_roles(mock_request, ["admin"])
        assert user is not None
        assert user.user_id == "user123"

    def test_require_roles_without_required_role(self):
        """Test require_roles raises ValueError when user lacks role."""
        user_data = {
            "userId": "user123",
            "userDetails": "john.doe@example.com",
            "userRoles": ["user"],
            "identityProvider": "aad"
        }

        json_str = json.dumps(user_data)
        encoded = base64.b64encode(json_str.encode()).decode()

        mock_request = Mock()
        mock_request.headers = {"x-ms-client-principal": encoded}

        with pytest.raises(ValueError, match="Required roles"):
            require_roles(mock_request, ["admin"])

    def test_require_roles_with_any_of_multiple_roles(self):
        """Test require_roles with user having any of multiple required roles."""
        user_data = {
            "userId": "user123",
            "userDetails": "john.doe@example.com",
            "userRoles": ["moderator"],
            "identityProvider": "aad"
        }

        json_str = json.dumps(user_data)
        encoded = base64.b64encode(json_str.encode()).decode()

        mock_request = Mock()
        mock_request.headers = {"x-ms-client-principal": encoded}

        user = require_roles(mock_request, ["admin", "moderator"])
        assert user is not None
        assert user.user_id == "user123"


class TestRequireAllRoles:
    """Test require_all_roles function."""

    def test_require_all_roles_with_all_required_roles(self):
        """Test require_all_roles with user having all required roles."""
        user_data = {
            "userId": "user123",
            "userDetails": "john.doe@example.com",
            "userRoles": ["user", "admin", "moderator"],
            "identityProvider": "aad"
        }

        json_str = json.dumps(user_data)
        encoded = base64.b64encode(json_str.encode()).decode()

        mock_request = Mock()
        mock_request.headers = {"x-ms-client-principal": encoded}

        user = require_all_roles(mock_request, ["user", "admin"])
        assert user is not None
        assert user.user_id == "user123"

    def test_require_all_roles_missing_some_roles(self):
        """Test require_all_roles raises ValueError when user lacks some roles."""
        user_data = {
            "userId": "user123",
            "userDetails": "john.doe@example.com",
            "userRoles": ["user"],
            "identityProvider": "aad"
        }

        json_str = json.dumps(user_data)
        encoded = base64.b64encode(json_str.encode()).decode()

        mock_request = Mock()
        mock_request.headers = {"x-ms-client-principal": encoded}

        with pytest.raises(ValueError, match="All required roles needed"):
            require_all_roles(mock_request, ["user", "admin"])


class TestCreateAuthResponse:
    """Test create_auth_response function."""

    def test_create_auth_response_success(self):
        """Test creating successful auth response."""
        user_data = {"userRoles": ["user"]}
        user = UserPrincipal(user_data)

        response = create_auth_response(200, "Success", user)

        assert response.status_code == 200
        assert response.mimetype == "application/json"

        # Parse response body
        body = json.loads(response.get_body().decode())
        assert body["message"] == "Success"
        assert body["status_code"] == 200
        assert "user" in body
        assert body["user"]["userRoles"] == ["user"]

    def test_create_auth_response_error(self):
        """Test creating error auth response."""
        response = create_auth_response(403, "Access denied")

        assert response.status_code == 403
        assert response.mimetype == "application/json"

        body = json.loads(response.get_body().decode())
        assert body["error"] == "Access denied"
        assert body["status_code"] == 403
        assert "user" not in body

    def test_create_auth_response_without_user(self):
        """Test creating auth response without user info."""
        response = create_auth_response(200, "Success")

        assert response.status_code == 200
        body = json.loads(response.get_body().decode())
        assert body["message"] == "Success"
        assert "user" not in body