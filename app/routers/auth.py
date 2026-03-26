from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import OTP, User
from app.schemas.auth import OTPRequest, OTPVerify
from app.schemas.user import UserOut
from app.services.email_service import send_otp_email, test_resend_connection
from app.utils.jwt import create_access_token
from app.utils.otp import generate_otp, hash_otp, verify_otp

router = APIRouter()


@router.post("/request-otp")
async def request_otp(body: OTPRequest, db: AsyncSession = Depends(get_db)):
    otp_plain = generate_otp()
    otp_hashed = hash_otp(otp_plain)
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

    await db.execute(delete(OTP).where(OTP.email == body.email))
    db.add(OTP(email=body.email, otp_hash=otp_hashed, expires_at=expires))
    await db.commit()

    sent = await send_otp_email(body.email, otp_plain)
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send OTP email")
    return {"message": "OTP sent"}


@router.post("/verify-otp")
async def verify_otp_endpoint(body: OTPVerify, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OTP).where(OTP.email == body.email))
    otp_record = result.scalar_one_or_none()

    if not otp_record:
        raise HTTPException(status_code=400, detail="No OTP found for this email")
    if otp_record.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP expired")
    if not verify_otp(body.otp, otp_record.otp_hash):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    await db.execute(delete(OTP).where(OTP.email == body.email))

    user_result = await db.execute(select(User).where(User.email == body.email))
    user = user_result.scalar_one_or_none()

    if not user:
        user = User(email=body.email, role="customer", is_verified=True)
        db.add(user)
        await db.flush()

    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.role)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
    )
    return {"message": "Verified", "role": user.role, "is_new": user.name is None}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out"}


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_verified=user.is_verified,
        created_at=user.created_at,
        profile_image=user.profile.profile_image if user.profile else None,
    )


@router.get("/test-email-service")
async def test_email_service():
    """Test email service connection and domain verification status."""
    return await test_resend_connection()
