from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User, Role
from app.models.profile import Student, Faculty, Mentor
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get_by_role(self, role: str) -> List[User]:
        return self.db.query(User).filter(User.role == role).all()

    def count_by_role(self, role: str) -> int:
        return self.db.query(User).filter(User.role == role).count()

    def count_total(self) -> int:
        return self.db.query(User).count()


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db: Session):
        super().__init__(Role, db)

    def get_by_name(self, name: str) -> Optional[Role]:
        return self.db.query(Role).filter(Role.name == name).first()
