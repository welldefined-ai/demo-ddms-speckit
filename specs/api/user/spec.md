# User Management API

## Purpose

The User Management API provides user account administration capabilities for the DDMS system. It enables the system owner to create new users with different roles, list all users, and delete user accounts. This API implements role-based access control with three roles: owner (system administrator), admin (device management), and read_only (view-only access).

## Base Configuration

**Base URL**: `/api/users`
**Authentication**: Required for all endpoints (Bearer token). Role restrictions apply to each endpoint.

## Endpoints

### POST /api/users

Create a new user account.

**Authentication**: Required (Owner only)

**Role Restrictions**: Only the system owner can create new users. Cannot create additional owner accounts.

**Request**:

```json
{
  "username": "john_doe",
  "password": "SecurePass123!",
  "role": "admin",
  "language_preference": "en"
}
```

**Request Fields**:

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `username` | string | Yes | 3-50 chars, alphanumeric + underscore | Username for the new account |
| `password` | string | Yes | Min 8 chars | Password for the new account |
| `role` | string | Yes | `admin` or `read_only` | User role (cannot create owner) |
| `language_preference` | string | No | `en` or `zh` | Language preference (default: `en`) |

**Username Validation**:
- Must be 3-50 characters long
- Can only contain letters, numbers, and underscores
- Must be unique across the system

**Password Requirements**:
- Minimum 8 characters
- Additional complexity requirements may be enforced by the system

**Responses**:

#### 201 Created

User created successfully.

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "john_doe",
  "role": "admin",
  "language_preference": "en",
  "created_at": "2025-10-20T10:30:00Z",
  "updated_at": "2025-10-20T10:30:00Z"
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | User UUID |
| `username` | string | Username |
| `role` | string | User role (admin or read_only) |
| `language_preference` | string | Language preference (en or zh) |
| `created_at` | string | Account creation timestamp (ISO 8601) |
| `updated_at` | string | Last update timestamp (ISO 8601) |

#### 400 Bad Request

Validation error (invalid username format, weak password, etc.).

```json
{
  "detail": "Username must be between 3 and 50 characters and contain only letters, numbers, and underscores"
}
```

#### 403 Forbidden

Attempting to create an owner account or not authorized as owner.

```json
{
  "detail": "Cannot create owner accounts. Only one owner is allowed."
}
```

Or:

```json
{
  "detail": "Access forbidden. Required roles: owner"
}
```

#### 409 Conflict

Username already exists.

```json
{
  "detail": "User with username 'john_doe' already exists"
}
```

---

### GET /api/users

List all users in the system.

**Authentication**: Required (Owner or Admin)

**Role Restrictions**: Only owner and admin roles can list users. Read-only users cannot access this endpoint.

**Responses**:

#### 200 OK

Returns array of all users.

```json
[
  {
    "id": "023e4567-e89b-12d3-a456-426614174000",
    "username": "admin",
    "role": "owner",
    "language_preference": "en",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  },
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "john_doe",
    "role": "admin",
    "language_preference": "en",
    "created_at": "2025-10-20T10:30:00Z",
    "updated_at": "2025-10-20T10:30:00Z"
  },
  {
    "id": "223e4567-e89b-12d3-a456-426614174001",
    "username": "jane_smith",
    "role": "read_only",
    "language_preference": "zh",
    "created_at": "2025-10-20T11:00:00Z",
    "updated_at": "2025-10-20T11:00:00Z"
  }
]
```

**Response Fields**: Same as POST / response for each user object.

#### 403 Forbidden

Insufficient permissions (read_only user attempting to list users).

```json
{
  "detail": "Access forbidden. Required roles: owner, admin"
}
```

---

### DELETE /api/users/{user_id}

Delete a user account.

**Authentication**: Required (Owner only)

**Role Restrictions**: Only the system owner can delete users. Cannot delete the owner account itself.

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | UUID | User UUID to delete |

**Responses**:

#### 204 No Content

User deleted successfully.

#### 400 Bad Request

Invalid user ID format.

```json
{
  "detail": "Invalid user ID format"
}
```

#### 403 Forbidden

Attempting to delete the owner account or not authorized as owner.

```json
{
  "detail": "Cannot delete the owner account"
}
```

Or:

```json
{
  "detail": "Access forbidden. Required roles: owner"
}
```

#### 404 Not Found

User not found.

```json
{
  "detail": "User with ID 123e4567-e89b-12d3-a456-426614174000 not found"
}
```

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| USER_001 | 400 | Invalid username format |
| USER_002 | 400 | Password does not meet minimum requirements |
| USER_003 | 400 | Invalid user ID format |
| USER_004 | 403 | Cannot create owner accounts |
| USER_005 | 403 | Cannot delete owner account |
| USER_006 | 403 | Insufficient permissions (not owner) |
| USER_007 | 403 | Insufficient permissions (not owner/admin) |
| USER_008 | 404 | User not found |
| USER_009 | 409 | Username already exists |

## Role-Based Access Control

The DDMS system implements three user roles with different permission levels:

### Owner Role
- **Permissions**: Full system access
- **Capabilities**:
  - Create and delete users
  - Full device management (create, update, delete)
  - Full group management
  - All read operations
- **Restrictions**: Only one owner account exists in the system

### Admin Role
- **Permissions**: Device and group management
- **Capabilities**:
  - View all users (cannot create/delete)
  - Full device management (create, update, delete)
  - Full group management
  - All read operations
- **Restrictions**: Cannot manage user accounts

### Read-Only Role
- **Permissions**: View-only access
- **Capabilities**:
  - View devices, groups, and readings
  - View real-time monitoring data
  - Export data
- **Restrictions**: Cannot create, update, or delete any resources; cannot view user list

## Security Considerations

1. **Owner Protection**: The owner account cannot be deleted through the API
2. **Role Elevation**: Cannot create additional owner accounts through the API
3. **Username Uniqueness**: Enforced at the database level
4. **Password Security**: Passwords are hashed using bcrypt before storage
5. **Session Management**: User deletion does not invalidate existing JWT tokens (tokens expire naturally)

## Related Specs

- **Capabilities**: User management (CAP-008), Role-based access control (CAP-009)
- **Data Models**: User model with role enumeration
- **Services**: user_service for account management
- **Dependencies**: Uses require_role dependency for authorization
