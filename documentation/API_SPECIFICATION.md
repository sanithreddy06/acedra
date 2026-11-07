# REST API Specification (Module 0 Foundation)

Base URL: `http://localhost:8000/api/v1`
Interactive Swagger Documentation: `http://localhost:8000/docs`
Alternative ReDoc: `http://localhost:8000/redoc`

---

### Authentication (`/auth`)

#### 1. `POST /auth/login`
- **Request Body**:
  ```json
  {
    "email": "student@smartcampus.edu",
    "password": "StudentPass123!"
  }
  ```
- **Success Response (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 7200,
    "user": {
      "id": 5,
      "email": "student@smartcampus.edu",
      "full_name": "Alex Mercer",
      "role": "student",
      "department_name": "Computer Science & Engineering",
      "roll_number": "CS22B001",
      "usn": "1RV22CS001",
      "cgpa": 8.84,
      "current_semester": 5
    }
  }
  ```

#### 2. `POST /auth/refresh`
- **Request Body**:
  ```json
  { "refresh_token": "eyJhbGciOi..." }
  ```

#### 3. `GET /auth/me`
- **Headers**: `Authorization: Bearer <access_token>`
- Returns complete authenticated profile.

#### 4. `POST /auth/logout`
- Invalidate session, logs audit trail.

---

### Dashboards (`/dashboards`)

#### 1. `GET /dashboards/me`
- **Headers**: `Authorization: Bearer <access_token>`
- Dynamically queries relational data for the user's role:
  - `student`: CGPA, Attendance, Active Courses, Faculty Mentor.
  - `faculty`: Allocated subjects, departmental students, avg attendance.
  - `mentor`: Assigned mentees, at-risk alerts, cohort CGPA average.
  - `admin`: Total users across roles, departments, system status, audit trail.
  - `placement_officer`: Eligible candidates, campus CGPA, conversion metrics.

---

### User Administration (`/users`)

#### 1. `GET /users/`
- **Headers**: `Authorization: Bearer <admin_token>`
- Returns list of registered platform accounts.

#### 2. `POST /users/`
- **Headers**: `Authorization: Bearer <admin_token>`
- **Request Body**:
  ```json
  {
    "email": "jordan.lee@smartcampus.edu",
    "password": "SecurePassword123!",
    "full_name": "Dr. Jordan Lee",
    "role": "faculty",
    "department_id": 1,
    "phone": "+1-555-0199"
  }
  ```
- Creates user, hashes password with bcrypt, initializes role profile, and writes audit event.

---

### Academic Configuration (`/academics` & `/departments`)

- `GET /departments/`: List academic departments.
- `GET /academics/semesters`: List configured terms.
- `GET /academics/subjects`: List course curriculum subjects.
- `GET /academics/assignments`: List faculty course allocations.
