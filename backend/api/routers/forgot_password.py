"""
E.V.E. Forgot Password Router — backend/api/routers/forgot_password.py

Flow:
  1. POST /api/forgot-password  { email }  -> sends OTP
  2. POST /api/verify-otp       { email, otp }  -> returns reset_token
  3. POST /api/reset-password   { reset_token, new_password }  -> updates password
"""
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
import os
import secrets
import string
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from core.database import get_connection
from core.security import hash_password

router = APIRouter(prefix="/api", tags=["forgot-password"])

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")


_otp_store: Dict[str, Tuple[str, datetime]]         = {}
_reset_token_store: Dict[str, Tuple[str, datetime]] = {}

OTP_TTL_MINUTES   = 10
TOKEN_TTL_MINUTES = 15


def _generate_otp() -> str:
    """Returns a fresh cryptographically random 6-digit code every call."""
    return "".join(secrets.choice(string.digits) for _ in range(6))


def _send_otp_email(to_email: str, otp: str) -> None:
    # Display with spaces: 4 8 3 9 1 2
    otp_display = " ".join(otp)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f6f6f6;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f6f6f6;padding:48px 16px;">
  <tr><td align="center">
    <table width="440" cellpadding="0" cellspacing="0"
           style="background:#ffffff;border-radius:12px;overflow:hidden;
                  border:1px solid #eee;max-width:100%;">

      <tr><td height="3" style="background:#FF14A5;font-size:0;line-height:0;">&nbsp;</td></tr>

      <tr><td style="padding:32px 32px 24px;">
        <div style="font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;
                    color:#FF14A5;margin-bottom:20px;font-family:-apple-system,sans-serif;">E.V.E.</div>
        <div style="font-size:18px;font-weight:600;color:#111;margin-bottom:6px;
                    font-family:-apple-system,sans-serif;">Password reset</div>
        <div style="font-size:12px;color:#aaa;font-family:-apple-system,sans-serif;">
          Use the code below to reset your password.
        </div>
      </td></tr>

      <tr><td style="padding:0 32px;"><div style="height:1px;background:#f0f0f0;"></div></td></tr>

      <tr><td style="padding:36px 32px;text-align:center;">
        <div style="font-size:40px;font-weight:300;letter-spacing:5px;color:#111;
                    font-family:'Courier New',monospace;margin-bottom:16px;">
          {otp_display}
        </div>
        <div style="font-size:11px;color:#bbb;font-family:-apple-system,sans-serif;">
          Expires in
          <span style="color:#FF14A5;font-weight:500;">{OTP_TTL_MINUTES} minutes</span>
        </div>
      </td></tr>

      <tr><td style="padding:0 32px;"><div style="height:1px;background:#f0f0f0;"></div></td></tr>

      <tr><td style="padding:20px 32px 28px;">
        <div style="font-size:11px;color:#ccc;line-height:1.6;font-family:-apple-system,sans-serif;">
          If you didn&rsquo;t request this, you can safely ignore this email.
          Your password won&rsquo;t change.
        </div>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "[E.V.E.] Your password reset code"
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
        s.ehlo(); s.starttls(); s.ehlo()
        s.login(SMTP_USERNAME, SMTP_PASSWORD)
        s.sendmail(SMTP_USERNAME, to_email, msg.as_string())


# ── Schemas ────────────────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    """Step 1. Always 200 to prevent email enumeration."""
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT user_id FROM users WHERE email = %s", (data.email,))
        user = cur.fetchone()
    finally:
        cur.close()
        conn.close()

    if user:
        otp = _generate_otp()   # fresh random code every single time
        _otp_store[data.email] = (otp, datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES))
        try:
            _send_otp_email(data.email, otp)
        except Exception as e:
            print(f"OTP email failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to send OTP email")

    return {"message": "If that email is registered, a reset code has been sent."}


@router.post("/verify-otp")
async def verify_otp(data: VerifyOTPRequest):
    """Step 2. Validate OTP, return reset_token."""
    entry = _otp_store.get(data.email)
    if not entry:
        raise HTTPException(status_code=400, detail="No OTP requested for this email")

    otp, expires_at = entry
    if datetime.now(timezone.utc) > expires_at:
        _otp_store.pop(data.email, None)
        raise HTTPException(status_code=400, detail="OTP has expired")

    if not secrets.compare_digest(data.otp.strip(), otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    _otp_store.pop(data.email, None)   # consume — can't reuse

    reset_token = secrets.token_urlsafe(32)
    _reset_token_store[reset_token] = (
        data.email,
        datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES),
    )
    return {"reset_token": reset_token}


@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    """Step 3. Set new password."""
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    entry = _reset_token_store.get(data.reset_token)
    if not entry:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    email, expires_at = entry
    if datetime.now(timezone.utc) > expires_at:
        _reset_token_store.pop(data.reset_token, None)
        raise HTTPException(status_code=400, detail="Reset token has expired")

    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE email = %s RETURNING user_id",
            (hash_password(data.new_password), email),
        )
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="User not found")
        conn.commit()
    except HTTPException:
        conn.rollback(); raise
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Password reset failed")
    finally:
        cur.close()
        conn.close()

    _reset_token_store.pop(data.reset_token, None)   # consume — can't reuse
    return {"message": "Password reset successfully"}