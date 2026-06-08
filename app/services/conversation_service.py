from sqlmodel import Session, select

from app.models.call_transcript import (
    CallConversation,
    CallTranscript
)


def save_conversation_message(
    call_sid: str,
    speaker: str,
    message: str,
    session: Session
) -> CallConversation:
    conversation = CallConversation(
        call_sid=call_sid,
        speaker=speaker,
        message=message
    )

    session.add(conversation)
    session.commit()
    session.refresh(conversation)

    return conversation


def get_conversation_messages(
    call_sid: str,
    session: Session
) -> list[CallConversation]:
    return session.exec(
        select(CallConversation)
        .where(CallConversation.call_sid == call_sid)
        .order_by(CallConversation.timestamp)
    ).all()


def generate_call_transcript(
    call_sid: str,
    session: Session
) -> CallTranscript | None:
    messages = get_conversation_messages(
        call_sid,
        session
    )

    if not messages:
        return None

    transcript_text = "\n".join(
        f"{message.speaker}: {message.message}"
        for message in messages
    )

    existing_transcript = session.exec(
        select(CallTranscript).where(
            CallTranscript.call_sid == call_sid
        )
    ).first()

    if existing_transcript:
        existing_transcript.complete_transcript = transcript_text
        session.add(existing_transcript)
        session.commit()
        session.refresh(existing_transcript)
        return existing_transcript

    transcript = CallTranscript(
        call_sid=call_sid,
        complete_transcript=transcript_text
    )

    session.add(transcript)
    session.commit()
    session.refresh(transcript)

    return transcript
