"""
Authentication utilities for Azure Functions with Static Web Apps integration
@author cascade-01
"""

import base64
import json
import logging
from typing import Any, Dict, List, Optional

from azure.functions import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class UserPrincipal:
    """Represents an authenticated user from Static Web Apps."""

    def __init__(self, data: Dict[str, Any]):
        self.user_id = data.get("userId", "")
        self.user_details = data.get("userDetails", "")
        self.user_roles = data.get("userRoles", [])
        self.identity_provider = data.get("identityProvider", "")

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.user_roles

    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.user_roles for role in roles)

    def has_all_roles(self, roles: List[str]) -> bool:
        """Check if user has all of the specified roles."""
        return all(role in self.user_roles for role in roles)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "userId": self.user_id,
            "userDetails": self.user_details,
            "userRoles": self.user_roles,
            "identityProvider": self.identity_provider,
        }


def get_user_principal(req: HttpRequest) -> Optional[UserPrincipal]:
    """
    Extract user principal from Static Web Apps headers.

    Static Web Apps passes authenticated user information in the
    x-ms-client-principal header as base64-encoded JSON.
    """
    try:
        # Get the client principal header
        client_principal = req.headers.get("x-ms-client-principal")
        if not client_principal:
            logger.debug("No x-ms-client-principal header found")
            return None

        # Decode base64 encoded JSON
        try:
            decoded = base64.b64decode(client_principal).decode("utf-8")
            user_data = json.loads(decoded)
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Failed to decode client principal: {e}")
            return None

        # Create UserPrincipal instance
        user_principal = UserPrincipal(user_data)
        logger.info(f"Authenticated user: {user_principal.user_details}")

        return user_principal

    except Exception as e:
        logger.error(f"Error extracting user principal: {e}")
        return None


def require_auth(req: HttpRequest) -> UserPrincipal:
    """
    Require authentication and return user principal.
    Raises ValueError if user is not authenticated.
    """
    user = get_user_principal(req)
    if not user:
        logger.warning("Authentication required but no user found")
        raise ValueError("Authentication required")
    return user


def require_roles(req: HttpRequest, required_roles: List[str]) -> UserPrincipal:
    """
    Require specific roles and return user principal.
    Raises ValueError if user doesn't have required roles.
    """
    user = require_auth(req)

    if not user.has_any_role(required_roles):
        logger.warning(
            f"User {user.user_details} lacks required roles: {required_roles}"
        )
        raise ValueError(f"Required roles: {required_roles}")

    logger.info(f"User {user.user_details} authorized with roles: {user.user_roles}")
    return user


def require_all_roles(req: HttpRequest, required_roles: List[str]) -> UserPrincipal:
    """
    Require all specified roles and return user principal.
    Raises ValueError if user doesn't have all required roles.
    """
    user = require_auth(req)

    if not user.has_all_roles(required_roles):
        logger.warning(
            f"User {user.user_details} lacks all required roles: {required_roles}"
        )
        raise ValueError(f"All required roles needed: {required_roles}")

    return user


def create_auth_response(
    status_code: int, message: str, user: Optional[UserPrincipal] = None
) -> HttpResponse:
    """Create standardized authentication response."""
    response_data = {
        "error" if status_code >= 400 else "message": message,
        "status_code": status_code,
    }

    if user:
        response_data["user"] = {
            "userDetails": user.user_details,
            "userRoles": user.user_roles,
        }

    return HttpResponse(
        json.dumps(response_data), status_code=status_code, mimetype="application/json"
    )


def log_auth_event(user: UserPrincipal, action: str, success: bool, details: str = ""):
    """Log authentication events for monitoring and auditing."""
    logger.info(
        f"Auth event: {action}",
        extra={
            "user_id": user.user_id,
            "user_details": user.user_details,
            "action": action,
            "success": success,
            "roles": user.user_roles,
            "details": details,
            "identity_provider": user.identity_provider,
        },
    )


def auth_decorator(required_roles: Optional[List[str]] = None):
    """
    Decorator for Azure Functions that require authentication.

    Usage:
    @auth_decorator(['administrator'])
    async def admin_function(req: HttpRequest) -> HttpResponse:
        # Function implementation
        pass
    """

    def decorator(func):
        async def wrapper(req: HttpRequest) -> HttpResponse:
            try:
                if required_roles:
                    user = require_roles(req, required_roles)
                else:
                    user = require_auth(req)

                # Add user to request for function access
                req.user = user

                # Call the original function
                return await func(req)

            except ValueError as e:
                return create_auth_response(403, str(e))
            except Exception as e:
                logger.error(f"Authentication error in {func.__name__}: {e}")
                return create_auth_response(500, "Authentication error")

        return wrapper

    return decorator


# Convenience decorators for common role requirements
def require_admin(func):
    """Decorator that requires administrator role."""
    return auth_decorator(["administrator"])(func)


def require_user(func):
    """Decorator that requires authenticated user (any role)."""
    return auth_decorator()(func)


def allow_anonymous(func):
    """Decorator that allows both authenticated and anonymous users."""

    async def wrapper(req: HttpRequest) -> HttpResponse:
        # Add user to request if available, but don't require it
        req.user = get_user_principal(req)
        return await func(req)

    return wrapper
