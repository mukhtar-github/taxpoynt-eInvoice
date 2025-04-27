# TaxPoynt eInvoice - Authentication & Authorization

## Overview
This document details the secure authentication and authorization implementation for the TaxPoynt eInvoice platform, designed to meet FIRS requirements and industry best practices.

## Features

### 1. Secure Authentication
- **JWT Token-based Authentication**: Stateless authentication using JWT tokens with appropriate expiration times.
- **Password Security**: Secure password hashing using bcrypt, with complexity requirements enforced (8+ characters, mixed case, numbers).
- **API Key Authentication**: Alternative authentication method for system integrations.
- **Email Verification**: Mandatory email verification process for new accounts.
- **Password Reset**: Secure password reset functionality with tokenized email links.

### 2. Multi-Tenant Authorization System
- **Role-Based Access Control**: Granular access control based on user roles:
  - `OWNER`: Full administrative access to an organization
  - `ADMIN`: Administrative access without owner privileges
  - `MEMBER`: Standard user access to organization resources
  - `SI_USER`: System integrator user with specific permissions
- **Organization-Based Multi-Tenancy**: Data isolation based on organization boundaries
- **Permission-Based Authorization**: Specific permissions mapped to user roles

## Technical Implementation

### Database Models
- **User**: Core user information with authentication metadata
- **Organization**: Organization/business entity details
- **OrganizationUser**: Many-to-many relationship between users and organizations with role details

### Authentication Flow
1. User registers with email and password
2. Verification email is sent to user's email address
3. User verifies email by clicking verification link
4. User can now authenticate using email/password to receive JWT token
5. JWT token is used for subsequent API requests
6. Token includes user identity and expiration information

### Authorization Flow
1. API requests include JWT token in Authorization header
2. System validates token and extracts user identity
3. Endpoint-specific middleware checks if user has required role/permissions
4. For organization-specific resources, system verifies user belongs to the organization
5. Request proceeds only if all authorization checks pass

### Security Considerations
- **Token Expiration**: Access tokens expire after 30 minutes, refresh tokens after 7 days
- **Password Security**: All passwords are hashed using bcrypt with appropriate work factors
- **Rate Limiting**: Authentication endpoints are rate-limited to prevent brute force attacks
- **CORS Protection**: Appropriate CORS settings to prevent cross-site request forgery

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user account
- `POST /api/v1/auth/login` - Authenticate and receive JWT token
- `GET /api/v1/auth/verify/{token}` - Verify email address
- `POST /api/v1/auth/password-reset` - Request password reset
- `POST /api/v1/auth/password-reset/confirm` - Reset password using token
- `GET /api/v1/auth/me` - Get current user information

### Organizations & Users
- `POST /api/v1/auth/organizations` - Create new organization
- `GET /api/v1/auth/organizations/{org_id}` - Get organization details
- `GET /api/v1/auth/me/organizations` - Get organizations for current user
- `GET /api/v1/auth/organizations/{org_id}/users` - Get users in organization
- `POST /api/v1/auth/organizations/{org_id}/users` - Add user to organization
- `DELETE /api/v1/auth/organizations/{org_id}/users/{user_id}` - Remove user from organization
- `PATCH /api/v1/auth/organizations/{org_id}/users/{user_id}/role` - Update user role

## Usage Examples

### Registration and Authentication

```python
# Registration
response = requests.post(
    "https://api.taxpoynt.com/api/v1/auth/register",
    json={
        "email": "user@example.com",
        "password": "SecureP@ssw0rd",
        "full_name": "John Doe"
    }
)

# Login
response = requests.post(
    "https://api.taxpoynt.com/api/v1/auth/login",
    data={
        "username": "user@example.com",
        "password": "SecureP@ssw0rd"
    }
)
token = response.json()["access_token"]

# Access protected resource
response = requests.get(
    "https://api.taxpoynt.com/api/v1/auth/me",
    headers={"Authorization": f"Bearer {token}"}
)
```

### Organization Management

```python
# Create organization
response = requests.post(
    "https://api.taxpoynt.com/api/v1/auth/organizations",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "name": "My Company",
        "tax_id": "12345678-0001",
        "email": "info@mycompany.com"
    }
)
org_id = response.json()["id"]

# Add user to organization
response = requests.post(
    f"https://api.taxpoynt.com/api/v1/auth/organizations/{org_id}/users",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "user_id": "user-uuid-here",
        "role": "MEMBER"
    }
)
```

## Dependencies
- FastAPI for API framework
- Passlib/bcrypt for password hashing
- Python-Jose for JWT token handling
- SQLAlchemy for database operations
- Emails for email delivery

## Security Compliance
- Follows OWASP security best practices
- Complies with FIRS e-invoicing security requirements
- Implements defense-in-depth security approach 