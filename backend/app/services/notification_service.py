"""In-app notifications: per-user inbox, read state, preferences and administrator broadcasts."""
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.models.intervention import Notification, NotificationPreference, NotificationType
from app.models.user import User


class NotificationService:
    """Manages multi-channel in-app notifications and user alert preferences."""

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: int,
        unread_only: bool = False,
        limit: int = 30,
    ) -> Tuple[List[Notification], int]:
        """Fetch user notifications and calculate unread count."""
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read.is_(False))

        unread_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        ).count()

        notifications = query.order_by(desc(Notification.created_at)).limit(limit).all()
        return notifications, unread_count

    @staticmethod
    def mark_notification_read(db: Session, notification_id: int, user_id: int) -> bool:
        """Mark single notification as read."""
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        ).first()
        if not notif:
            return False

        notif.is_read = True
        notif.read_at = utcnow()
        db.commit()
        return True

    @staticmethod
    def mark_all_notifications_read(db: Session, user_id: int) -> int:
        """Mark all unread notifications as read for a user."""
        unread = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        ).all()

        now = utcnow()
        for n in unread:
            n.is_read = True
            n.read_at = now

        db.commit()
        return len(unread)

    @staticmethod
    def get_or_create_preferences(db: Session, user_id: int) -> NotificationPreference:
        """Retrieve user notification preferences or create defaults."""
        pref = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
        if not pref:
            pref = NotificationPreference(
                user_id=user_id,
                email_alerts_enabled=True,
                risk_notifications=True,
                recommendation_notifications=True,
                intervention_notifications=True,
                placement_notifications=True,
                announcement_notifications=True,
                updated_at=utcnow(),
            )
            db.add(pref)
            db.commit()
            db.refresh(pref)
        return pref

    @staticmethod
    def update_preferences(db: Session, user_id: int, updates: Dict[str, Any]) -> NotificationPreference:
        """Update notification preferences."""
        pref = NotificationService.get_or_create_preferences(db, user_id)
        for key, val in updates.items():
            if val is not None and hasattr(pref, key):
                setattr(pref, key, val)
        pref.updated_at = utcnow()
        db.commit()
        db.refresh(pref)
        return pref

    @staticmethod
    def broadcast_announcement(
        db: Session,
        title: str,
        message: str,
        target_role: Optional[str] = None,
        department_id: Optional[int] = None,
    ) -> int:
        """Broadcast administrative announcement to users."""
        query = db.query(User).filter(User.is_active.is_(True))
        if target_role:
            query = query.filter(User.role == target_role)
        if department_id:
            query = query.filter(User.department_id == department_id)

        users = query.all()
        now = utcnow()
        for u in users:
            notif = Notification(
                user_id=u.id,
                title=title,
                message=message,
                notification_type=NotificationType.ADMINISTRATIVE_ANNOUNCEMENT.value,
                severity="INFO",
                is_read=False,
                created_at=now,
            )
            db.add(notif)

        db.commit()
        return len(users)
