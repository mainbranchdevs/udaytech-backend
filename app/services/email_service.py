import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger(__name__)


async def send_otp_email(to_email: str, otp: str) -> bool:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(
            "SMTP credentials are not set. OTP not sent. For dev, use this code: %s (for %s)",
            otp,
            to_email,
        )
        return True  # allow dev flow without SMTP

    message = EmailMessage()
    message["Subject"] = "Your Udaya Tech verification code"
    message["From"] = settings.FROM_EMAIL or settings.SMTP_USER
    message["To"] = to_email
    message.set_content(
        (
            "Your verification code is: "
            f"{otp}\n\nThis code expires in {settings.OTP_EXPIRE_MINUTES} minutes."
        )
    )
    message.add_alternative(
        (
            "<h2>Your verification code</h2>"
            f"<p style='font-size:32px;font-weight:bold;letter-spacing:8px'>{otp}</p>"
            f"<p>This code expires in {settings.OTP_EXPIRE_MINUTES} minutes.</p>"
        ),
        subtype="html",
    )

    def _send_email() -> None:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=20) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(message)

    try:
        await asyncio.to_thread(_send_email)
        return True
    except Exception as e:
        logger.exception("Failed to send OTP email to %s: %s", to_email, e)
        return False
