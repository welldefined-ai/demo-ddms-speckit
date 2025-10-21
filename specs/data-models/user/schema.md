# User

## Purpose

Stores user account information with authentication credentials and role-based access control for the DDMS application.

## Schema

### Entity: User

Represents a user account with authentication and authorization data.

**Table**: `users`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | PRIMARY KEY, NOT NULL | Unique user identifier |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL | Unique username for login |
| `password_hash` | VARCHAR(255) | NOT NULL | Bcrypt hashed password (cost factor 12) |
| `role` | ENUM('OWNER', 'ADMIN', 'READ_ONLY') | NOT NULL | User role for RBAC |
| `language_preference` | VARCHAR(2) | NOT NULL, DEFAULT 'en' | UI language preference (en, zh) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Account creation timestamp |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, DEFAULT NOW() | Last modification timestamp |

**Indexes**:
- `ix_users_username` ON `username` (for fast login lookups)

**Relationships**:
```typescript
User {
  hasMany: []
  belongsTo: []
}
```

## Validation Rules

### Rule: Username Uniqueness

- **MUST** be unique across all users
- **MUST NOT** exceed 50 characters
- **MUST** be provided (NOT NULL)

### Rule: Password Requirements

- **MUST** be hashed using bcrypt with cost factor 12
- **MUST** store only password_hash, never plaintext password
- **MUST NOT** expose password_hash in API responses

### Rule: Role Assignment

- **MUST** be one of: OWNER, ADMIN, READ_ONLY
- **MUST** be assigned on user creation
- OWNER: Full system access including user management
- ADMIN: Device and group management, no user management
- READ_ONLY: View-only access to devices and data

### Rule: Language Preference

- **MUST** be 2-letter ISO 639-1 language code
- Supported values: "en" (English), "zh" (Chinese)
- Defaults to "en" if not specified

### Rule: Timestamp Management

- `created_at` automatically set on record creation
- `updated_at` automatically updated on any field modification

## Related Specs

- **Capabilities**: `capabilities/user-authentication/spec.md`
- **APIs**: `api/authentication/spec.md`, `api/user/spec.md`
