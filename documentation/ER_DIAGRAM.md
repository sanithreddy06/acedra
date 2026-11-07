# Entity-Relationship Model (Module 0 Database Schema)

The core relational database model powers user authentication, role hierarchies, departmental structures, academic curricula, faculty allocations, and security audit logs.

```mermaid
erDiagram
    USERS ||--o{ AUDIT_LOGS : generates
    USERS ||--o| STUDENTS : profile
    USERS ||--o| FACULTY : profile
    USERS ||--o| MENTORS : profile
    ROLES ||--o{ USERS : assigns
    DEPARTMENTS ||--o{ USERS : members
    DEPARTMENTS ||--o{ SUBJECTS : offers
    DEPARTMENTS ||--o{ STUDENTS : enrolls
    DEPARTMENTS ||--o{ FACULTY : employs
    DEPARTMENTS ||--o{ MENTORS : employs
    FACULTY ||--o{ FACULTY_COURSE_ASSIGNMENTS : teaches
    SUBJECTS ||--o{ FACULTY_COURSE_ASSIGNMENTS : assigned_in
    SEMESTERS ||--o{ FACULTY_COURSE_ASSIGNMENTS : scheduled_in
    MENTORS ||--o{ STUDENTS : guides
    STUDENTS ||--o{ STUDENT_MENTOR_ASSIGNMENTS : history
    MENTORS ||--o{ STUDENT_MENTOR_ASSIGNMENTS : guides

    USERS {
        int id PK
        string email UK
        string hashed_password
        string full_name
        string role
        int department_id FK
        boolean is_active
        boolean is_verified
        datetime created_at
        datetime updated_at
    }

    ROLES {
        int id PK
        string name UK
        string display_name
        string description
        json permissions
    }

    DEPARTMENTS {
        int id PK
        string code UK
        string name
        string description
        string hod_name
    }

    STUDENTS {
        int id PK
        int user_id FK
        string roll_number UK
        string usn UK
        int department_id FK
        int current_semester
        int batch_year
        string section
        float cgpa
        float attendance_percentage
        string placement_status
        int assigned_mentor_id FK
    }

    FACULTY {
        int id PK
        int user_id FK
        string employee_id UK
        int department_id FK
        string designation
        string specialization
    }

    MENTORS {
        int id PK
        int user_id FK
        string employee_id UK
        int department_id FK
        string designation
        int max_mentees
    }

    SEMESTERS {
        int id PK
        string name
        string academic_year
        int semester_number
        boolean is_current
        date start_date
        date end_date
    }

    SUBJECTS {
        int id PK
        string code UK
        string name
        int department_id FK
        int semester_number
        int credits
        string subject_type
    }

    FACULTY_COURSE_ASSIGNMENTS {
        int id PK
        int faculty_id FK
        int subject_id FK
        int semester_id FK
        string section
        string academic_year
    }

    STUDENT_MENTOR_ASSIGNMENTS {
        int id PK
        int student_id FK
        int mentor_id FK
        string academic_year
        int semester
        boolean is_active
        date assigned_date
    }

    AUDIT_LOGS {
        int id PK
        int user_id FK
        string action
        string resource_type
        string resource_id
        string ip_address
        string user_agent
        json details
        datetime created_at
    }

    SYSTEM_SETTINGS {
        int id PK
        string key UK
        json value
        string description
        string category
        int updated_by FK
        datetime updated_at
    }
```
