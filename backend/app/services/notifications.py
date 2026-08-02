"""Create in-app notifications and optional email delivery."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.models import Notification, NotificationChannel, User
from app.services.email import EmailService


class NotificationService:
    def __init__(self) -> None:
        self.email_service = EmailService()

    def notify(
        self,
        db: Session,
        *,
        user_id: UUID,
        title: str,
        body: str,
        link: str | None = None,
        related_session_id: UUID | None = None,
        send_email: bool = True,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            channel=NotificationChannel.IN_APP,
            title=title,
            body=body,
            link=link,
            related_session_id=related_session_id,
            is_read=False,
            email_sent=False,
        )
        db.add(notification)
        db.flush()

        if send_email:
            user = db.get(User, user_id)
            if user and user.email:
                sent = self.email_service.send(user.email, title, body)
                notification.email_sent = sent
                if sent:
                    notification.channel = NotificationChannel.EMAIL

        db.commit()
        db.refresh(notification)
        return notification

    def list_for_user(self, db: Session, user_id: UUID, unread_only: bool = False) -> list[Notification]:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read.is_(False))
        return query.order_by(Notification.created_at.desc()).all()

    def mark_read(self, db: Session, notification: Notification) -> Notification:
        notification.is_read = True
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification
