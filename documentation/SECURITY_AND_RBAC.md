# Security Architecture & Role-Based Access Control (RBAC)

## 1. Authentication Lifecycle

1. **Password Security**:
   - Salted passwords hashed with native `bcrypt` (12 calculation rounds).
   - Strict 72-byte boundary enforced with character encoding protections.
   - Passwords never stored or logged in plain text.

2. **Tokenization (JWT)**:
   - Claims include `sub` (User ID), `role` (Role identifier), `exp` (Expiry), and `type` (`access` vs `refresh`).
   - Configurable token lifetimes (default: 120 minutes access token, 7 days refresh token).
   - Cryptographically signed with `HS256` using server-side secret key.

3. **Protection against Data Leakage**:
   - Password hashes excluded from all Pydantic serialization schemas (`UserOut`, `UserProfileOut`).
   - Generic error messages for failed authentication to prevent username enumeration attacks.

## 2. Role-Based Access Control (RBAC) Matrix

| Resource / Endpoint | Student | Faculty | Mentor | Administrator / HOD | Placement Officer |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `POST /api/v1/auth/login` | Yes | Yes | Yes | Yes | Yes |
| `GET /api/v1/auth/me` | Yes | Yes | Yes | Yes | Yes |
| `GET /api/v1/dashboards/me` | Yes (Student view) | Yes (Faculty view) | Yes (Mentor view) | Yes (Admin view) | Yes (Placement view) |
| `GET /api/v1/users/` | No | No | No | **Yes** | No |
| `POST /api/v1/users/` | No | No | No | **Yes** | No |
| `PATCH /api/v1/users/{id}` | Self only | Self only | Self only | **Yes (Any)** | Self only |
| `GET /api/v1/departments/` | Yes | Yes | Yes | Yes | Yes |
| `POST /api/v1/departments/`| No | No | No | **Yes** | No |
| `GET /api/v1/academics/semesters` | Yes | Yes | Yes | Yes | Yes |
| `POST /api/v1/academics/subjects` | No | No | No | **Yes** | No |
| `GET /api/v1/audit-logs/` | No | No | No | **Yes** | No |
| `GET /api/v1/settings/` | No | No | No | **Yes** | No |
| `PATCH /api/v1/settings/{key}` | No | No | No | **Yes** | No |

## 3. Rate Limiting

- Powered by `slowapi` utilizing the client's real remote IP (with reverse proxy `X-Forwarded-For` header analysis).
- Default API limit: 120 requests/minute.
- Strict authentication endpoint limit: 20 login attempts/minute.
- Exceeded rate triggers HTTP 429 Too Many Requests with descriptive reset window.

## 4. Audit Logging

Every critical security and data lifecycle event automatically registers into the persistent `audit_logs` table:
- `LOGIN_SUCCESS`, `LOGIN_FAILED`
- `USER_CREATED`, `USER_UPDATED`
- `PASSWORD_RESET_REQUESTED`, `PASSWORD_RESET_SUCCESS`
- `LOGOUT`
- Captures actor ID, IP address, user-agent string, and contextual event metadata in JSON.
