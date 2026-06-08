from datetime import datetime

from sqlmodel import Session, select

from app.models.call_logs import CallLog
from app.models.call_recording import CallRecording


def start_or_get_call_log(
    call_sid: str,
    caller_number: str,
    session: Session
) -> CallLog:
    call_log = session.exec(
        select(CallLog).where(
            CallLog.call_sid == call_sid
        )
    ).first()

    if call_log:
        return call_log

    call_log = CallLog(
        call_sid=call_sid,
        caller_number=caller_number,
        call_status="in_progress"
    )

    session.add(call_log)
    session.commit()
    session.refresh(call_log)

    return call_log


def update_call_status(
    call_sid: str,
    call_status: str,
    duration_seconds: int | None,
    session: Session
) -> CallLog | None:
    call_log = session.exec(
        select(CallLog).where(
            CallLog.call_sid == call_sid
        )
    ).first()

    if not call_log:
        return None

    call_log.call_status = call_status

    if call_status in {"completed", "busy", "failed", "no-answer", "canceled"}:
        call_log.ended_at = datetime.utcnow()

    if duration_seconds is not None:
        call_log.duration_seconds = duration_seconds

    session.add(call_log)
    session.commit()
    session.refresh(call_log)

    return call_log


def save_call_recording(
    call_sid: str,
    recording_url: str,
    session: Session
) -> CallRecording:
    recording = CallRecording(
        call_sid=call_sid,
        recording_url=recording_url
    )

    session.add(recording)
    session.commit()
    session.refresh(recording)

    return recording
