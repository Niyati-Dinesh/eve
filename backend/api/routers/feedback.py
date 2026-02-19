"""
E.V.E. Feedback Router — backend/api/routers/feedback.py
"""

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from api.deps import get_current_user

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

FEEDBACK_TO   = "ignite.techteam33@gmail.com"


class FeedbackPayload(BaseModel):
    rating: int
    message: str
    conversation_id: str | None = None
    ai_message_snippet: str | None = None


def _stars(rating: int) -> str:
    return "★" * rating + "☆" * (5 - rating)


@router.post("/send")
async def send_feedback(
    payload: FeedbackPayload,
    current_user: dict = Depends(get_current_user),
):
    rating_label = ["", "Poor", "Fair", "Good", "Great", "Excellent"][min(payload.rating, 5)]
    sent_at      = datetime.now(timezone.utc).strftime("%B %d, %Y &middot; %H:%M UTC")
    conv         = payload.conversation_id or "&mdash;"

    snippet_block = ""
    if payload.ai_message_snippet:
        safe = payload.ai_message_snippet[:300].replace("<", "&lt;").replace(">", "&gt;")
        if len(payload.ai_message_snippet) > 300:
            safe += "&hellip;"
        snippet_block = f"""
      <tr><td style="padding:14px 32px 0;">
        <div style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;
                    color:#ccc;margin-bottom:4px;font-family:-apple-system,sans-serif;">AI Response</div>
        <div style="font-size:12px;color:#888;line-height:1.65;font-style:italic;
                    font-family:-apple-system,sans-serif;">&ldquo;{safe}&rdquo;</div>
      </td></tr>"""

    message_block = ""
    if payload.message and payload.message.strip():
        safe_msg = payload.message.replace("<", "&lt;").replace(">", "&gt;")
        message_block = f"""
      <tr><td style="padding:14px 32px 0;">
        <div style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;
                    color:#ccc;margin-bottom:4px;font-family:-apple-system,sans-serif;">Message</div>
        <div style="font-size:13px;color:#555;line-height:1.65;
                    font-family:-apple-system,sans-serif;">{safe_msg}</div>
      </td></tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f6f6f6;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f6f6f6;padding:48px 16px;">
  <tr><td align="center">
    <table width="480" cellpadding="0" cellspacing="0"
           style="background:#ffffff;border-radius:12px;overflow:hidden;
                  border:1px solid #eee;max-width:100%;">

      <tr><td height="3" style="background:#FF14A5;font-size:0;line-height:0;">&nbsp;</td></tr>

      <tr><td style="padding:32px 32px 24px;">
        <div style="font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;
                    color:#FF14A5;margin-bottom:20px;font-family:-apple-system,sans-serif;">E.V.E.</div>
        <div style="font-size:18px;font-weight:600;color:#111;margin-bottom:6px;
                    font-family:-apple-system,sans-serif;">New feedback</div>
        <div style="font-size:12px;color:#aaa;font-family:-apple-system,sans-serif;">{sent_at}</div>
      </td></tr>

      <tr><td style="padding:0 32px;"><div style="height:1px;background:#f0f0f0;"></div></td></tr>

      <tr><td style="padding:24px 32px 0;">
        <div style="font-size:20px;color:#FF14A5;letter-spacing:2px;margin-bottom:4px;">
          {_stars(payload.rating)}
        </div>
        <div style="font-size:12px;font-weight:500;color:#555;font-family:-apple-system,sans-serif;">
          {rating_label} &mdash; {payload.rating} / 5
        </div>
      </td></tr>

      <tr><td style="padding:20px 32px 0;">
        <div style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;
                    color:#ccc;margin-bottom:4px;font-family:-apple-system,sans-serif;">From</div>
        <div style="font-size:13px;color:#333;font-family:-apple-system,sans-serif;">
          {current_user['email']}
        </div>
      </td></tr>

      <tr><td style="padding:14px 32px 0;">
        <div style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;
                    color:#ccc;margin-bottom:4px;font-family:-apple-system,sans-serif;">Conversation</div>
        <div style="font-size:12px;color:#999;font-family:monospace;">{conv}</div>
      </td></tr>

      {snippet_block}
      {message_block}

      <tr><td style="padding:28px 32px;">
        <div style="font-size:11px;color:#ddd;font-family:-apple-system,sans-serif;">
          E.V.E. feedback system
        </div>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[E.V.E.] {payload.rating}/5 \u00b7 {rating_label} \u2014 from {current_user['email']}"
    msg["From"]    = SMTP_USERNAME
    msg["To"]      = FEEDBACK_TO
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.ehlo(); s.starttls(); s.ehlo()
            s.login(SMTP_USERNAME, SMTP_PASSWORD)
            s.sendmail(SMTP_USERNAME, FEEDBACK_TO, msg.as_string())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Feedback sent successfully"}