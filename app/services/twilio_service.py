import os
import traceback

from fastapi.responses import Response
from sqlmodel import Session
from twilio.twiml.voice_response import (
    Gather,
    VoiceResponse
)

from app.services.conversation_service import save_conversation_message


PUBLIC_BASE_URL = os.getenv(
    "PUBLIC_BASE_URL",
    "https://unworshipped-fearfully-chanell.ngrok-free.dev"
).rstrip("/")

PROCESS_SPEECH_URL = f"{PUBLIC_BASE_URL}/process-speech"
VOICE_URL = f"{PUBLIC_BASE_URL}/voice"
SPEECH_HINTS = (
    "heart, heart pain, heart disease, chest pain, cardiac, cardio, "
    "skin, skin allergy, skin disease, rash, acne, pimple, derma, "
    "dermatology, dermatologist, headache, migraine, brain, nerve, "
    "seizure, dizziness, child, baby, fever, cough, bone, joint, "
    "knee pain, back pain, fracture, shoulder pain, doctor, "
    "appointment, tomorrow, today"
)


def safe_save_ai_message(
    call_sid: str,
    message: str,
    session: Session
):
    try:
        save_conversation_message(
            call_sid=call_sid,
            speaker="AI",
            message=message,
            session=session
        )
    except Exception:
        print("AI CONVERSATION SAVE FAILED")
        traceback.print_exc()
        session.rollback()


def xml_response(response: VoiceResponse) -> Response:
    return Response(
        content=str(response),
        media_type="application/xml"
    )


def gather_response(
    call_sid: str,
    message: str,
    session: Session
) -> Response:
    safe_save_ai_message(
        call_sid,
        message,
        session
    )

    response = VoiceResponse()
    gather = Gather(
        input="speech",
        action=PROCESS_SPEECH_URL,
        method="POST",
        timeout=10,
        speech_timeout="auto",
        action_on_empty_result=True,
        language="en-IN",
        hints=SPEECH_HINTS
    )

    gather.say(message)
    response.append(gather)

    return xml_response(response)


def final_response(
    call_sid: str,
    message: str,
    session: Session
) -> Response:
    safe_save_ai_message(
        call_sid,
        message,
        session
    )

    response = VoiceResponse()
    response.say(message)
    response.hangup()

    return xml_response(response)
