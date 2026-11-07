from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.security import get_password_hash, verify_password
from app.models.user import User, Role, UserRole
from app.models.profile import Student, Faculty, Mentor
from app.schemas.user import UserCreate, UserUpdate
from app.repositories.user_repo import UserRepository
from app.repositories.audit_repo import AuditRepository


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)

    def create_user(self, user_in: UserCreate, creator_id: Optional[int] = None) -> User:
        existing = self.user_repo.get_by_email(user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email '{user_in.email}' already exists."
            )

        # Hash password securely
        hashed_password = get_password_hash(user_in.password)

        role_obj = self.db.query(Role).filter(Role.name == user_in.role).first()
        role_id = role_obj.id if role_obj else None

        user = User(
            email=user_in.email.lower(),
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            phone=user_in.phone,
            role=user_in.role,
            role_id=role_id,
            department_id=user_in.department_id,
            is_active=user_in.is_active,
            is_verified=True,
            avatar_url=user_in.avatar_url
        )
        self.db.add(user)
        self.db.flush()

        # Attach role-specific profile based on role
        if user_in.role == UserRole.STUDENT.value:
            roll = user_in.roll_number or f"STU-{user.id:04d}"
            usn = user_in.usn or f"1RV24CS{user.id:03d}"
            dept_id = user_in.department_id or 1
            student = Student(
                user_id=user.id,
                roll_number=roll,
                usn=usn,
                department_id=dept_id,
                current_semester=5,
                batch_year=2024,
                section="A",
                cgpa=8.5,
                attendance_percentage=92.0,
                placement_status="Eligible"
            )
            self.db.add(student)
        elif user_in.role == UserRole.FACULTY.value:
            emp_id = user_in.employee_id or f"FAC-{user.id:03d}"
            dept_id = user_in.department_id or 1
            faculty = Faculty(
                user_id=user.id,
                employee_id=emp_id,
                department_id=dept_id,
                designation=user_in.designation or "Associate Professor",
                specialization="Computer Science & Engineering"
            )
            self.db.add(faculty)
        elif user_in.role == UserRole.MENTOR.value:
            emp_id = user_in.employee_id or f"MNT-{user.id:03d}"
            dept_id = user_in.department_id or 1
            mentor = Mentor(
                user_id=user.id,
                employee_id=emp_id,
                department_id=dept_id,
                designation=user_in.designation or "Lead Student Mentor",
                max_mentees=30
            )
            self.db.add(mentor)

        self.db.commit()
        self.db.refresh(user)

        self.audit_repo.log(
            action="USER_CREATED",
            user_id=creator_id,
            resource_type="user",
            resource_id=str(user.id),
            details={"email": user.email, "role": user.role}
        )
        return user

    def update_user(self, user_id: int, user_in: UserUpdate, actor_id: Optional[int] = None) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user_in.full_name is not None:
            user.full_name = user_in.full_name
        if user_in.phone is not None:
            user.phone = user_in.phone
        if user_in.department_id is not None:
            user.department_id = user_in.department_id
        if user_in.is_active is not None:
            user.is_active = user_in.is_active
        if user_in.avatar_url is not None:
            user.avatar_url = user_in.avatar_url

        self.db.commit()
        self.db.refresh(user)

        self.audit_repo.log(
            action="USER_UPDATED",
            user_id=actor_id,
            resource_type="user",
            resource_id=str(user.id),
            details={"updated_fields": list(user_in.model_dump(exclude_unset=True).keys())}
        )
        return user

    def change_password(self, user_id: int, old_pass: str, new_pass: str) -> bool:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(old_pass, user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        user.hashed_password = get_password_hash(new_pass)
        self.db.commit()

        self.audit_repo.log(
            action="PASSWORD_CHANGED",
            user_id=user.id,
            resource_type="user",
            resource_id=str(user.id)
        )
        return True
