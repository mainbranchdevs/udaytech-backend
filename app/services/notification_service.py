import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification


async def create_notification(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    title: str,
    message: str,
    type: str = "info",
) -> Notification:
    notif = Notification(user_id=user_id, title=title, message=message, type=type)
    db.add(notif)
    await db.flush()
    return notif
