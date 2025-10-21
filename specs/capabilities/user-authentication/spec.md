# User Authentication and Authorization

## Purpose

Provides secure user authentication using JWT tokens with role-based access control (RBAC) supporting three user roles: Owner, Admin, and Read-Only.

## Requirements

### Requirement: User Login

The system SHALL authenticate users with username and password credentials.

#### Scenario: Successful login with valid credentials

- **WHEN** user provides valid username and password
- **THEN** system queries users table for username
- **AND** system verifies password using bcrypt hash comparison
- **AND** system generates JWT access token (30 minute expiry)
- **AND** system generates refresh token (7 day expiry)
- **AND** system returns access_token, refresh_token, and user details

#### Scenario: Failed login with invalid username

- **WHEN** user provides username not in database
- **THEN** system returns 401 Unauthorized
- **AND** error message: "Invalid credentials"
- **AND** does not reveal whether username or password was incorrect

#### Scenario: Failed login with invalid password

- **WHEN** user provides valid username but incorrect password
- **THEN** system returns 401 Unauthorized
- **AND** error message: "Invalid credentials"
- **AND** same response as invalid username (prevent user enumeration)

### Requirement: JWT Token Generation

The system SHALL generate JSON Web Tokens for authenticated sessions.

#### Scenario: Access token creation

- **WHEN** user successfully authenticates
- **THEN** system creates JWT with HS256 algorithm
- **AND** payload includes: {sub: username, user_id: UUID, role: enum}
- **AND** token signed with JWT_SECRET_KEY
- **AND** expiration set to 30 minutes (configurable via ACCESS_TOKEN_EXPIRE_MINUTES)

#### Scenario: Refresh token creation

- **WHEN** user successfully authenticates
- **THEN** system creates refresh token JWT
- **AND** expiration set to 7 days
- **AND** stored in httpOnly secure cookie
- **AND** prevents JavaScript access for security

### Requirement: Token Validation

The system SHALL validate JWT tokens on protected endpoint requests.

#### Scenario: Valid token authorization

- **WHEN** request includes Authorization: Bearer {valid_token}
- **THEN** system validates token signature using JWT_SECRET_KEY
- **AND** system checks token not expired
- **AND** system extracts user_id and role from payload
- **AND** request proceeds to endpoint handler

#### Scenario: Expired token rejection

- **WHEN** request includes expired token
- **THEN** system returns 401 Unauthorized
- **AND** error message indicates token expired
- **AND** client should use refresh endpoint

#### Scenario: Invalid token signature

- **WHEN** request includes token with invalid signature
- **THEN** system returns 401 Unauthorized
- **AND** error message indicates invalid token

#### Scenario: Missing token

- **WHEN** request to protected endpoint without Authorization header
- **THEN** system returns 401 Unauthorized
- **AND** error message indicates authentication required

### Requirement: Token Refresh

The system SHALL allow refreshing expired access tokens using valid refresh tokens.

#### Scenario: Refresh access token

- **WHEN** user submits valid refresh token
- **THEN** system validates refresh token signature and expiration
- **AND** system generates new access token (30 minute expiry)
- **AND** system optionally generates new refresh token
- **AND** system returns new access_token

#### Scenario: Invalid refresh token

- **WHEN** user submits expired or invalid refresh token
- **THEN** system returns 401 Unauthorized
- **AND** user must login again with credentials

### Requirement: User Logout

The system SHALL allow users to end their authenticated session.

#### Scenario: Logout with token invalidation

- **WHEN** user logs out
- **THEN** system invalidates access token (adds to blacklist or expires)
- **AND** system clears refresh token cookie
- **AND** system returns success confirmation
- **AND** subsequent requests with old token fail authorization

### Requirement: Password Management

The system SHALL securely store and validate user passwords using bcrypt.

#### Scenario: Password hashing on user creation

- **WHEN** new user account created
- **THEN** system hashes password using bcrypt (cost factor 12)
- **AND** system stores only password_hash, never plaintext
- **AND** password_hash stored in users.password_hash column

#### Scenario: Password change

- **WHEN** authenticated user requests password change
- **THEN** system validates old password using bcrypt
- **AND** system hashes new password
- **AND** system updates password_hash in database
- **AND** system optionally invalidates existing tokens (force re-login)

### Requirement: Role-Based Access Control (RBAC)

The system SHALL enforce three-tier role hierarchy: Owner > Admin > ReadOnly.

#### Scenario: Owner role permissions

- **WHEN** user with role=OWNER accesses endpoint
- **THEN** system allows full access to all operations
- **AND** can create/delete users
- **AND** can create/update/delete devices and groups
- **AND** can view all data

#### Scenario: Admin role permissions

- **WHEN** user with role=ADMIN accesses endpoint
- **THEN** system allows device and group management
- **AND** can create/update/delete devices
- **AND** can create/update/delete groups
- **AND** can view all data
- **AND** cannot create/delete users

#### Scenario: ReadOnly role permissions

- **WHEN** user with role=READ_ONLY accesses endpoint
- **THEN** system allows viewing devices, readings, groups
- **AND** can export data
- **AND** cannot create/update/delete any resources
- **AND** cannot access user management

#### Scenario: Authorization check failure

- **WHEN** user attempts operation without required role
- **THEN** system returns 403 Forbidden
- **AND** error message indicates insufficient permissions

### Requirement: RBAC Decorator Implementation

The system SHALL use @require_roles decorator to enforce endpoint authorization.

#### Scenario: Endpoint with role requirement

- **WHEN** endpoint decorated with @require_roles([Role.ADMIN, Role.OWNER])
- **THEN** system validates authenticated user's role
- **AND** allows access if user role in allowed list
- **AND** returns 403 if user role not in allowed list

#### Scenario: Public endpoint (no role check)

- **WHEN** endpoint has no @require_roles decorator
- **THEN** system allows access without authentication
- **AND** used for SSE stream, login endpoint

### Requirement: User Account Management

The system SHALL allow Owner role to manage user accounts.

#### Scenario: Create new user

- **WHEN** owner creates user with username, password, role
- **THEN** system validates username unique
- **AND** system hashes password with bcrypt
- **AND** system creates user record
- **AND** system returns user details (no password_hash)

#### Scenario: List users

- **WHEN** owner or admin requests user list
- **THEN** system returns all users with id, username, role, timestamps
- **AND** system excludes password_hash from response

#### Scenario: Delete user

- **WHEN** owner deletes user
- **THEN** system removes user record from database
- **AND** user's existing tokens become invalid

### Requirement: Language Preference

The system SHALL store user language preference for internationalization.

#### Scenario: User language selection

- **WHEN** user sets language_preference (default "en")
- **THEN** system stores 2-letter language code in users table
- **AND** frontend uses preference for i18n (en, zh)

### Requirement: Security Headers and CORS

The system SHALL configure security headers and CORS for web application.

#### Scenario: CORS configuration

- **WHEN** frontend makes API request from different origin
- **THEN** system validates origin against CORS_ORIGINS environment variable
- **AND** system includes appropriate Access-Control-Allow-* headers
- **AND** development allows localhost:3000, production uses actual domain

#### Scenario: Secure cookie attributes

- **WHEN** setting refresh token cookie
- **THEN** cookie has httpOnly=True (prevent JavaScript access)
- **AND** cookie has secure=True in production (HTTPS only)
- **AND** cookie has SameSite=Strict (CSRF protection)

## Related Specs

- **Data Models**: `data-models/user/schema.md`
- **APIs**: `api/authentication/spec.md`, `api/user/spec.md`
- **Architecture**: `architecture/ddms-system/spec.md`
