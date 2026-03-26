import asyncio
import logging
import smtplib
from email.message import EmailMessage

import resend

from app.config import settings

logger = logging.getLogger(__name__)


async def test_resend_connection() -> dict:
    """Test Resend API connection and domain verification status."""
    if not settings.RESEND_API_KEY:
        return {"status": "error", "message": "RESEND_API_KEY not set"}

    try:
        resend.api_key = settings.RESEND_API_KEY

        # Try to get domains to check verification status
        domains = resend.Domains.list()
        domain_status = {}
        for domain in domains.get("data", []):
            domain_status[domain["name"]] = {
                "verified": domain.get("verified", False),
                "status": domain.get("status", "unknown")
            }

        return {
            "status": "success",
            "api_key_prefix": settings.RESEND_API_KEY[:10] + "...",
            "from_email": settings.FROM_EMAIL,
            "domains": domain_status
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "api_key_prefix": settings.RESEND_API_KEY[:10] + "..." if settings.RESEND_API_KEY else "None"
        }


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

        logger.info("Attempting to send email with API key: %s... and FROM_EMAIL: %s",
                   settings.RESEND_API_KEY[:10] + "..." if settings.RESEND_API_KEY else "None",
                   settings.FROM_EMAIL)

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
