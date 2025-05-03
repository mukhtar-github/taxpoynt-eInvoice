# TaxPoynt eInvoice - Authentication Testing Guide

This document provides instructions for testing the authentication flow in the TaxPoynt eInvoice system using Postman or curl.

## Prerequisites

- Backend server running (default: http://localhost:8000)
- Postman installed (optional, for GUI testing)
- curl available (for command-line testing)

## Authentication Endpoints

### 1. User Registration

**Endpoint:** `POST /api/v1/auth/register`

#### Postman

1. Create a new POST request to `http://localhost:8000/api/v1/auth/register`
2. Set Content-Type header to `application/json`
3. Set the request body to:
```json
{
  "email": "test@example.com",
  "password": "SecureP@ss123",
  "full_name": "Test User"
}
```
4. Send the request

#### curl

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecureP@ss123",
    "full_name": "Test User"
  }'
```

**Expected Response:**
```json
{
  "id": "uuid-string",
  "email": "test@example.com",
  "full_name": "Test User",
  "is_active": true,
  "role": "si_user",
  "is_email_verified": false,
  "created_at": "2025-05-03T14:30:00"
}
```

### 2. Email Verification

**Endpoint:** `GET /api/v1/auth/verify/{token}`

After registering, check the user's email (or console logs in development) for the verification link containing the token.

#### Postman

1. Create a new GET request to `http://localhost:8000/api/v1/auth/verify/{token}`
   (Replace `{token}` with the actual token received)
2. Send the request

#### curl

```bash
curl -X GET http://localhost:8000/api/v1/auth/verify/{token}
```

**Expected Response:**
```json
{
  "message": "Email verification successful. You can now log in."
}
```

### 3. User Login

**Endpoint:** `POST /api/v1/auth/login`

#### Postman

1. Create a new POST request to `http://localhost:8000/api/v1/auth/login`
2. Set Content-Type header to `application/x-www-form-urlencoded`
3. Add form data:
   - username: test@example.com
   - password: SecureP@ss123
4. Send the request

#### curl

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=SecureP@ss123"
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "user_id": "uuid-string",
  "email": "test@example.com"
}
```

### 4. Using the Access Token

To access protected endpoints, include the access token in the Authorization header.

#### Postman

1. Create a new GET request to any protected endpoint (e.g., `http://localhost:8000/api/v1/auth/me`)
2. Add an Authorization header with value `Bearer {access_token}`
   (Replace `{access_token}` with the actual token received from login)
3. Send the request

#### curl

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### 5. Refresh Token

**Endpoint:** `POST /api/v1/auth/refresh`

When the access token expires, use the refresh token to get a new one.

#### Postman

1. Create a new POST request to `http://localhost:8000/api/v1/auth/refresh`
2. Set Content-Type header to `application/json`
3. Set the request body to:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```
4. Send the request

#### curl

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "user_id": "uuid-string"
}
```

### 6. Logout

**Endpoint:** `POST /api/v1/auth/logout`

#### Postman

1. Create a new POST request to `http://localhost:8000/api/v1/auth/logout`
2. Add an Authorization header with value `Bearer {access_token}`
3. Send the request

#### curl

```bash
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

**Expected Response:**
```json
{
  "detail": "Successfully logged out"
}
```

## Testing the Role-Based Access Control

The system implements role-based access control with the following roles:
- `owner`: Full administrative access
- `admin`: Administrative access with limitations
- `member`: Standard user access
- `si_user`: System integrator user

To test role-based access:

1. Register and login with a test user
2. Note that new users are assigned the `si_user` role by default
3. Access endpoints with different role requirements to verify proper authorization

## Troubleshooting

### Common Issues

1. **Invalid Credentials**
   - Ensure you're using the correct email and password
   - Check that the user has been properly registered

2. **Unauthorized Access**
   - Verify that your access token is valid and not expired
   - Ensure the token is correctly formatted in the Authorization header
   - Check that the user has the required role for the resource

3. **Invalid Token Format**
   - Ensure the token is sent with the format `Bearer {token}`
   - Check that there are no extra spaces or characters in the token

4. **Email Verification Issues**
   - Confirm that you're using the exact verification link sent to the email
   - Tokens are typically valid for 48 hours; request a new one if expired

## Next Steps

After testing the basic authentication flow, you can proceed to test:

1. Password reset functionality
2. User management endpoints
3. Role-based access to other API resources
4. Integration with front-end authentication components
