# Azure AD Authentication Configuration

## Overview

This document provides step-by-step instructions for configuring Azure Active Directory (Azure AD) authentication for the Steve's Mom AI Chatbot Static Web App.

## Prerequisites

- Azure Static Web App deployed
- Azure AD tenant access
- Global Administrator or Application Administrator role

## Azure AD App Registration

### 1. Create App Registration

1. Navigate to **Azure Active Directory** in Azure Portal
2. Go to **App registrations** > **New registration**
3. Configure the registration:
   - **Name**: `Steve's Mom AI Chatbot`
   - **Supported account types**: `Accounts in this organizational directory only`
   - **Redirect URI**: `https://<your-static-web-app>.azurestaticapps.net/.auth/login/aad/callback`

### 2. Configure Authentication

1. Go to **Authentication** in your app registration
2. Add platform configuration:
   - **Platform**: Web
   - **Redirect URIs**:
     - `https://<your-static-web-app>.azurestaticapps.net/.auth/login/aad/callback`
     - `https://stevesmom.cannasol.tech/.auth/login/aad/callback` (if using custom domain)
   - **Logout URL**: `https://<your-static-web-app>.azurestaticapps.net/.auth/logout`

3. Configure token settings:
   - **Access tokens**: Checked
   - **ID tokens**: Checked
   - **Allow public client flows**: No

### 3. Create Client Secret

1. Go to **Certificates & secrets**
2. Click **New client secret**
3. Configure:
   - **Description**: `Static Web App Authentication`
   - **Expires**: `24 months`
4. **Copy the secret value** (you won't see it again)

### 4. Configure API Permissions

1. Go to **API permissions**
2. Add the following permissions:
   - **Microsoft Graph**:
     - `User.Read` (Delegated)
     - `profile` (Delegated)
     - `openid` (Delegated)
     - `email` (Delegated)

3. Grant admin consent for the permissions

## Static Web App Configuration

### 1. Environment Variables

Add these application settings to your Static Web App:

```bash
AAD_CLIENT_ID=<your-application-id>
AAD_CLIENT_SECRET=<your-client-secret>
AAD_TENANT_ID=<your-tenant-id>
```

### 2. Update staticwebapp.config.json

The authentication configuration is already included in the config file:

```json
{
  "auth": {
    "identityProviders": {
      "azureActiveDirectory": {
        "userDetailsClaim": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
        "registration": {
          "openIdIssuer": "https://login.microsoftonline.com/common/v2.0",
          "clientIdSettingName": "AAD_CLIENT_ID",
          "clientSecretSettingName": "AAD_CLIENT_SECRET"
        }
      }
    }
  }
}
```

## Role-Based Access Control

### 1. Define Custom Roles

Create custom roles in your `staticwebapp.config.json`:

```json
{
  "routes": [
    {
      "route": "/admin/*",
      "allowedRoles": ["administrator"]
    },
    {
      "route": "/api/admin/*",
      "allowedRoles": ["administrator"]
    },
    {
      "route": "/api/chat/*",
      "allowedRoles": ["anonymous", "authenticated", "user"]
    }
  ]
}
```

### 2. Assign Roles to Users

Via Azure Portal:

1. Go to your Static Web App
2. Navigate to **Role management**
3. Click **Invite**
4. Enter user email and select role
5. Send invitation

Via Azure CLI:

```bash
az staticwebapp users invite \
  --name <static-web-app-name> \
  --resource-group <resource-group> \
  --authentication-provider aad \
  --user-details <user-email> \
  --roles "administrator"
```

## Frontend Integration

### 1. Authentication State Management

```typescript
// src/services/authService.ts
export interface UserInfo {
  userId: string;
  userDetails: string;
  userRoles: string[];
  identityProvider: string;
}

export class AuthService {
  async getUserInfo(): Promise<UserInfo | null> {
    try {
      const response = await fetch('/.auth/me');
      const data = await response.json();
      
      if (data.clientPrincipal) {
        return {
          userId: data.clientPrincipal.userId,
          userDetails: data.clientPrincipal.userDetails,
          userRoles: data.clientPrincipal.userRoles,
          identityProvider: data.clientPrincipal.identityProvider
        };
      }
      return null;
    } catch (error) {
      console.error('Failed to get user info:', error);
      return null;
    }
  }

  login(): void {
    window.location.href = '/.auth/login/aad';
  }

  logout(): void {
    window.location.href = '/.auth/logout';
  }
}
```

### 2. Protected Route Component

```typescript
// src/components/ProtectedRoute.tsx
import React, { useEffect, useState } from 'react';
import { AuthService, UserInfo } from '../services/authService';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRoles?: string[];
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRoles = [] 
}) => {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const authService = new AuthService();

  useEffect(() => {
    const checkAuth = async () => {
      const userInfo = await authService.getUserInfo();
      setUser(userInfo);
      setLoading(false);
    };
    checkAuth();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return (
      <div className="auth-required">
        <h2>Authentication Required</h2>
        <button onClick={() => authService.login()}>
          Sign in with Azure AD
        </button>
      </div>
    );
  }

  if (requiredRoles.length > 0) {
    const hasRequiredRole = requiredRoles.some(role => 
      user.userRoles.includes(role)
    );
    
    if (!hasRequiredRole) {
      return (
        <div className="access-denied">
          <h2>Access Denied</h2>
          <p>You don't have permission to access this resource.</p>
        </div>
      );
    }
  }

  return <>{children}</>;
};
```

## API Authentication

### 1. Function App Integration

```python
# backend/functions/auth_utils.py
import json
from typing import Optional, List, Dict, Any
from azure.functions import HttpRequest

class UserPrincipal:
    def __init__(self, data: Dict[str, Any]):
        self.user_id = data.get('userId', '')
        self.user_details = data.get('userDetails', '')
        self.user_roles = data.get('userRoles', [])
        self.identity_provider = data.get('identityProvider', '')

def get_user_principal(req: HttpRequest) -> Optional[UserPrincipal]:
    """Extract user principal from Static Web App headers."""
    try:
        # Static Web Apps passes user info in headers
        client_principal = req.headers.get('x-ms-client-principal')
        if not client_principal:
            return None
            
        # Decode base64 encoded JSON
        import base64
        decoded = base64.b64decode(client_principal).decode('utf-8')
        user_data = json.loads(decoded)
        
        return UserPrincipal(user_data)
    except Exception:
        return None

def require_auth(req: HttpRequest) -> UserPrincipal:
    """Require authentication and return user principal."""
    user = get_user_principal(req)
    if not user:
        raise ValueError("Authentication required")
    return user

def require_roles(req: HttpRequest, required_roles: List[str]) -> UserPrincipal:
    """Require specific roles and return user principal."""
    user = require_auth(req)
    
    if not any(role in user.user_roles for role in required_roles):
        raise ValueError(f"Required roles: {required_roles}")
    
    return user
```

### 2. Protected Function Example

```python
# backend/functions/admin_function.py
import json
import azure.functions as func
from .auth_utils import require_roles

async def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # Require administrator role
        user = require_roles(req, ['administrator'])
        
        # Admin-only functionality here
        return func.HttpResponse(
            json.dumps({
                "message": "Admin access granted",
                "user": user.user_details
            }),
            mimetype="application/json"
        )
        
    except ValueError as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=403,
            mimetype="application/json"
        )
```

## Security Best Practices

### 1. Token Validation

- Always validate tokens server-side
- Check token expiration
- Verify audience and issuer claims
- Use HTTPS only

### 2. Role Management

- Follow principle of least privilege
- Regularly audit user roles
- Use groups for role assignment when possible
- Implement role hierarchy

### 3. Session Management

- Configure appropriate token lifetimes
- Implement proper logout functionality
- Clear client-side state on logout
- Monitor for suspicious activity

## Troubleshooting

### Common Issues

1. **Redirect URI Mismatch**
   - Ensure redirect URIs match exactly in Azure AD
   - Include both default and custom domains

2. **CORS Issues**
   - Configure CORS in Function App settings
   - Allow Static Web App domain

3. **Token Validation Failures**
   - Check client secret expiration
   - Verify tenant ID configuration
   - Ensure proper permissions granted

### Debugging Commands

```bash
# Test authentication endpoint
curl -i https://<your-app>.azurestaticapps.net/.auth/me

# Check user roles
curl -H "Authorization: Bearer <token>" \
  https://<your-app>.azurestaticapps.net/.auth/me

# Test protected API
curl -H "Authorization: Bearer <token>" \
  https://<your-app>.azurestaticapps.net/api/admin/status
```

## Monitoring and Logging

### 1. Azure AD Sign-in Logs

Monitor authentication events in Azure AD:

- Go to **Azure Active Directory** > **Sign-in logs**
- Filter by application name
- Review failed sign-ins and errors

### 2. Application Insights

Track authentication metrics:

- User sign-in success/failure rates
- Token validation errors
- Role-based access patterns
- Session duration analytics

### 3. Custom Logging

```python
# Add to your functions
import logging

logger = logging.getLogger(__name__)

def log_auth_event(user: UserPrincipal, action: str, success: bool):
    logger.info(f"Auth event: {action}", extra={
        'user_id': user.user_id,
        'user_details': user.user_details,
        'action': action,
        'success': success,
        'roles': user.user_roles
    })
```
