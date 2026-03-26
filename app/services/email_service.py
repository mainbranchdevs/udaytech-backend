import asyncio
import logging
import smtplib
from email.message import EmailMessage

import resend

from app.config import settings

logger = logging.getLogger(__name__)


async def send_otp_email(to_email: str, otp: str) -> bool:
    if not settings.RESEND_API_KEY:
        logger.warning(
            "RESEND_API_KEY is not set. OTP not sent. For dev, use this code: %s (for %s)",
            otp,
            to_email,
        )
        return True  # allow dev flow without email

    def _send_email() -> None:
        resend.api_key = settings.RESEND_API_KEY

        params = {
            "from": settings.FROM_EMAIL,
            "to": to_email,
            "subject": "Your Udaya Tech verification code",
            "html": (
                "<h2>Your verification code</h2>"
                f"<p style='font-size:32px;font-weight:bold;letter-spacing:8px'>{otp}</p>"
                f"<p>This code expires in {settings.OTP_EXPIRE_MINUTES} minutes.</p>"
            ),
        }
        resend.Emails.send(params)

    try:
        await asyncio.to_thread(_send_email)
        return True
    except resend.exceptions.ResendError as e:
        if "domain is not verified" in str(e):
            logger.warning(
                "Email domain not verified in Resend. OTP not sent. "
                "For dev/testing, use this code: %s (for %s). "
                "To fix: Verify your domain at https://resend.com/domains",
                otp,
                to_email,
            )
            return True  # allow flow to continue in dev
        else:
            logger.exception("Failed to send OTP email to %s: %s", to_email, e)
            return False
    except Exception as e:
        logger.exception("Failed to send OTP email to %s: %s", to_email, e)
        return False
