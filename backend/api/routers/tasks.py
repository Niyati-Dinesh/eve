"""
E.V.E. Tasks Router - backend/api/routers/tasks.py

Architecture:
  React (5173)  →  FastAPI backend (8000)  →  Master Controller (8001)

Duplicate fix:
  The master controller also calls store_message internally, causing each
  message to appear twice in the DB. We fix this in get_history by using
  a DISTINCT ON (role, content) query ordered by message_id to keep only
  the FIRST occurrence of each (role, content) pair, preserving order.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from typing import Optional, List
import httpx
import uuid
import os
import asyncio

from api.deps import get_current_user
from core.database import (
    create_or_get_conversation,
    store_message,
    get_last_n_messages,
    get_connection,
    create_task,
    store_execution_result,
    log_system_event,
)
from core.config import MASTER_HOST, MASTER_PORT

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

MASTER_HOST = os.getenv("MASTER_HOST", "localhost")
MASTER_PORT = os.getenv("MASTER_PORT", "8001")
MASTER_URL = f"http://{MASTER_HOST}:{MASTER_PORT}"


# ─── Master readiness check ───────────────────────────────────────────────────

async def wait_for_master(retries: int = 10, delay: float = 1.5) -> bool:
    async with httpx.AsyncClient(timeout=3.0) as client:
        for attempt in range(retries):
            try:
                resp = await client.get(f"{MASTER_URL}/health")
                if resp.status_code == 200:
                    if attempt > 0:
                        print(f"   ✅ Master ready after {attempt + 1} attempts")
                    return True
            except Exception:
                pass
            if attempt < retries - 1:
                await asyncio.sleep(delay)
    return False


# ─── Send a message ───────────────────────────────────────────────────────────

@router.post("/message")
async def send_message(
    message: str = Form(""),
    conversation_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[]),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user["user_id"])

    if not conversation_id:
        conversation_id = f"{user_id}_{uuid.uuid4().hex[:12]}"
    create_or_get_conversation(conversation_id, int(user_id))

    # Store user message here (master may also store it — deduplicated on read)
    store_message(conversation_id, "user", message)

    task_id = None
    try:
        task_id = create_task(
            user_id=int(user_id),
            task_desc=message[:500],
            task_type="general",
            priority=1,
        )
        log_system_event("info", f"Task created: {task_id} for user {user_id}")
    except Exception as e:
        print(f"⚠️  Could not create task record: {e}")

    master_ready = await wait_for_master(retries=10, delay=1.5)
    if not master_ready:
        log_system_event("error", f"Master not ready after retries - user {user_id}")
        raise HTTPException(
            status_code=503,
            detail=(
                f"Master controller on port {MASTER_PORT} is not responding. "
                "Make sure start_system.py has been run and wait a few seconds before retrying."
            ),
        )

    ai_response = ""
    extra_file = None
    master_success = False

    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            form_data = {
                "user_id": user_id,
                "message": message,
                "conversation_id": conversation_id,
            }

            file_tuples = []
            for f in files:
                if f.filename:
                    content = await f.read()
                    file_tuples.append(
                        ("files", (f.filename, content, f.content_type or "application/octet-stream"))
                    )

            response = await client.post(
                f"{MASTER_URL}/process_message",
                data=form_data,
                files=file_tuples if file_tuples else None,
            )
            response.raise_for_status()
            data = response.json()

        ai_response = data.get("response", "")
        extra_file = data.get("file")
        master_success = True

    except httpx.TimeoutException:
        log_system_event("error", "Master controller timeout")
        raise HTTPException(status_code=504, detail="Master controller timed out")

    except httpx.HTTPStatusError as e:
        log_system_event("error", f"Master HTTP error: {e.response.status_code}")
        raise HTTPException(status_code=502, detail=f"Master controller error: {e.response.text[:200]}")

    except Exception as e:
        err_detail = str(e)
        log_system_event("error", f"Master unreachable: {err_detail[:200]}")
        raise HTTPException(
            status_code=503,
            detail=(
                f"Master controller unreachable: {err_detail}\n\n"
                "Make sure start_system.py has been run and the master is on port "
                f"{MASTER_PORT}."
            ),
        )

    finally:
        if ai_response:
            store_message(conversation_id, "assistant", ai_response)

        if task_id:
            try:
                store_execution_result(
                    task_id=task_id,
                    agent_id=1,
                    output_data=ai_response or "No response",
                    success=master_success,
                    execution_time=0.0,
                )
            except Exception as e:
                print(f"⚠️  Could not store execution result: {e}")

    payload = {"response": ai_response, "conversation_id": conversation_id}
    if extra_file:
        payload["file"] = extra_file

    return JSONResponse(payload)


# ─── Fetch conversation history  ────────────────────────────────

@router.get("/history/{conversation_id}")
def get_history(
    conversation_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
):
    """
    Return deduplicated message history for a conversation.

    Uses a two-step dedup:
    1. SQL: select the MINIMUM message_id for each (role, content) pair so
       that if the master controller also stored the same message, only the
       first DB row survives. Results are returned in chronological order.
    2. Python: walk the ordered list and skip any message whose (role, content)
       was already emitted — catches duplicates that differ only in timestamp.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                MIN(message_id)  AS message_id,
                role,
                content,
                MIN(timestamp)   AS timestamp
            FROM messages
            WHERE conversation_id = %s
            GROUP BY role, content
            ORDER BY MIN(message_id) ASC
            LIMIT %s
            """,
            (conversation_id, limit),
        )
        rows = [dict(r) for r in cur.fetchall()]
    finally:
        cur.close()
        conn.close()

    # Python-level guard: skip consecutive same-role duplicates
    # (handles edge case where content differs by whitespace only)
    deduped = []
    last_role = None
    last_content = None
    for row in rows:
        normalized = (row["content"] or "").strip()
        if row["role"] == last_role and normalized == last_content:
            continue
        deduped.append(row)
        last_role = row["role"]
        last_content = normalized

    return {"conversation_id": conversation_id, "messages": deduped}


# ─── List sidebar conversations ───────────────────────────────────────────────

@router.get("/conversations")
def list_conversations(current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT
                c.conversation_id,
                c.started_at,
                c.last_updated,
                COUNT(DISTINCT m.message_id) AS message_count,
                (
                    SELECT content
                    FROM messages
                    WHERE conversation_id = c.conversation_id
                      AND role = 'user'
                    ORDER BY timestamp ASC
                    LIMIT 1
                ) AS preview
            FROM conversations c
            LEFT JOIN messages m ON m.conversation_id = c.conversation_id
            WHERE c.user_id = %s
              AND c.is_active = TRUE
            GROUP BY c.conversation_id, c.started_at, c.last_updated
            ORDER BY c.last_updated DESC
            LIMIT 30
            """,
            (current_user["user_id"],),
        )
        rows = cur.fetchall()
        return {"conversations": [dict(r) for r in rows]}
    finally:
        cur.close()
        conn.close()


# ─── Delete / archive a conversation ─────────────────────────────────────────

@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            UPDATE conversations
            SET is_active = FALSE
            WHERE conversation_id = %s
              AND user_id = %s
            """,
            (conversation_id, current_user["user_id"]),
        )
        conn.commit()
        return {"message": "Conversation deleted"}
    finally:
        cur.close()
        conn.close()