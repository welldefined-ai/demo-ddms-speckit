# Authentication API

## Purpose

The Authentication API provides user authentication, session management, and password management capabilities for the DDMS system. It handles user login, logout, token refresh, and password changes with JWT-based authentication and rate limiting for security.

## Base Configuration

**Base URL**: `/api/auth`
**Authentication**: Mixed (login/refresh endpoints do not require authentication, logout/change-password do)

## Endpoints

### POST /api/auth/login

Authenticate a user and obtain access tokens.

**Authentication**: None (public endpoint)

**Rate Limiting**: 5 attempts per 15 minutes per username

**Request**:

```json
{
  "username": "string",
  "password": "string"
}
```

**Request Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Username (minimum 1 character) |
| `password` | string | Yes | Password (minimum 1 character) |

**Responses**:

#### 200 OK

Successful authentication. Returns access token, refresh token, and user data. Also sets a secure httponly cookie with the refresh token (7 day expiration).

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "admin",
    "role": "owner"
  }
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | JWT access token for API authentication |
| `token_type` | string | Token type (always "bearer") |
| `refresh_token` | string | JWT refresh token for obtaining new access tokens |
| `user` | object | User information |
| `user.user_id` | string | User UUID |
| `user.username` | string | Username |
| `user.role` | string | User role (owner/admin/read_only) |

**Cookies Set**:
- `refresh_token`: Secure, httponly cookie with 7 day expiration (samesite=lax, secure=true)

#### 401 Unauthorized

Invalid credentials provided.

```json
{
  "detail": "Invalid username or password"
}
```

#### 429 Too Many Requests

Rate limit exceeded for this username.

```json
{
  "detail": "Too many login attempts. Please try again in 15 minutes."
}
```

---

### POST /api/auth/logout

Logout the current user and invalidate session.

**Authentication**: Required (Bearer token)

**Request**: None (empty body)

**Responses**:

#### 200 OK

Successfully logged out. Clears the refresh token cookie.

```json
{
  "message": "Successfully logged out"
}
```

#### 401 Unauthorized

Invalid or missing authentication token.

```json
{
  "detail": "Invalid or expired token"
}
```

---

### POST /api/auth/refresh

Refresh the access token using a valid existing token. This endpoint rotates both access and refresh tokens for security.

**Authentication**: Required (Bearer token)

**Request**: None (empty body, token provided in Authorization header)

**Responses**:

#### 200 OK

Successfully refreshed tokens. Returns new access and refresh tokens. Updates the refresh token cookie.

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | New JWT access token |
| `token_type` | string | Token type (always "bearer") |
| `refresh_token` | string | New JWT refresh token |

**Cookies Set**:
- `refresh_token`: Updated secure, httponly cookie with 7 day expiration

#### 401 Unauthorized

Invalid or expired token provided.

```json
{
  "detail": "Invalid or expired token"
}
```

---

### POST /api/auth/change-password

Change the password for the currently authenticated user.

**Authentication**: Required (Bearer token)

**Request**:

```json
{
  "old_password": "string",
  "new_password": "string"
}
```

**Request Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `old_password` | string | Yes | Current password (minimum 1 character) |
| `new_password` | string | Yes | New password (minimum 8 characters) |

**Responses**:

#### 200 OK

Password changed successfully.

```json
{
  "message": "Password changed successfully"
}
```

#### 400 Bad Request

New password does not meet requirements.

```json
{
  "detail": "Password must be at least 8 characters long"
}
```

#### 401 Unauthorized

Old password is incorrect or authentication token is invalid.

```json
{
  "detail": "Old password is incorrect"
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| AUTH_001 | 401 | Invalid username or password |
| AUTH_002 | 401 | Invalid or expired token |
| AUTH_003 | 401 | Invalid token payload |
| AUTH_004 | 401 | Old password is incorrect |
| AUTH_005 | 429 | Too many login attempts (rate limited) |
| AUTH_006 | 400 | Password does not meet minimum requirements |

## Security Features

- **JWT-based authentication**: Stateless token-based authentication
- **Token rotation**: Both access and refresh tokens are rotated on refresh
- **Secure cookies**: Refresh tokens stored in httponly, secure cookies
- **Rate limiting**: Login endpoint rate limited to 5 attempts per 15 minutes per username
- **Password requirements**: Minimum 8 characters for new passwords

## Related Specs

- **Capabilities**: User authentication and session management (CAP-001)
- **Data Models**: User model with authentication fields
- **Dependencies**: Uses JWT token verification from utils/auth module
