from uuid import UUID
import traceback
import re
from datetime import datetime

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import Response
from sqlmodel import Session
from twilio.twiml.voice_response import (
    VoiceResponse,
    Gather
)

from app.database.db import engine
from app.models.doctor import Doctor

from app.services.appointment_service import (
    create_voice_appointment,
    find_doctor_from_speech,
    find_doctors_by_department,
    get_available_slots,
    is_slot_available,
    parse_appointment_time
)
from app.services.call_service import (
    save_call_recording,
    start_or_get_call_log,
    update_call_status
)
from app.services.conversation_service import (
    generate_call_transcript,
    save_conversation_message
)
from app.services.disease_classifier_service import (
    DISEASE_SPEECH_HINTS,
    detect_department
)
from app.services.twilio_service import (
    final_response,
    gather_response,
    safe_save_ai_message
)

router = APIRouter()

conversation_state = {}

PROCESS_SPEECH_URL = "https://unworshipped-fearfully-chanell.ngrok-free.dev/process-speech"
VOICE_URL = "https://unworshipped-fearfully-chanell.ngrok-free.dev/voice"
SPEECH_HINTS = DISEASE_SPEECH_HINTS


def get_form_value(form_data, key: str, default: str = "") -> str:
    value = form_data.get(key)
    return str(value).strip() if value is not None else default


def normalize_confirmation(user_speech: str) -> str:
    normalized = user_speech.lower()
    normalized = re.sub(r"[^a-z0-9 ]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def is_yes(user_speech: str) -> bool:
    normalized = normalize_confirmation(user_speech)
    words = set(normalized.split())

    negative_phrases = {
        "not correct",
        "no correct",
        "not right",
        "wrong",
        "incorrect"
    }

    if "no" in words or any(phrase in normalized for phrase in negative_phrases):
        return False

    yes_words = {
        "yes",
        "ya",
        "yah",
        "yeah",
        "yep",
        "yup",
        "haan",
        "ha",
        "correct",
        "right",
        "confirm",
        "confirmed",
        "ok",
        "okay"
    }

    yes_phrases = {
        "yes it is correct",
        "yes correct",
        "that is correct",
        "it is correct",
        "spelling is correct",
        "name is correct",
        "yes confirm",
        "yes confirmed"
    }

    return (
        normalized in yes_words
        or bool(words.intersection(yes_words))
        or any(phrase in normalized for phrase in yes_phrases)
    )


def is_no(user_speech: str) -> bool:
    normalized = normalize_confirmation(user_speech)
    words = set(normalized.split())

    no_words = {
        "no",
        "nope",
        "nah",
        "nahi",
        "wrong",
        "incorrect",
        "not correct"
    }

    no_phrases = {
        "no it is wrong",
        "that is wrong",
        "it is wrong",
        "spelling is wrong",
        "name is wrong",
        "not correct"
    }

    return (
        normalized in no_words
        or bool(words.intersection(no_words))
        or any(phrase in normalized for phrase in no_phrases)
    )


def spell_text(value: str) -> str:
    letters = [
        character.upper()
        for character in value
        if character.isalpha()
    ]

    return ", ".join(letters)


def clean_spelled_name(user_speech: str) -> str:
    cleaned = (
        user_speech
        .replace(",", " ")
        .replace(".", " ")
        .replace("-", " ")
    )

    parts = [
        part.strip()
        for part in cleaned.split()
        if part.strip()
    ]

    if parts and all(len(part) == 1 for part in parts):
        return "".join(parts).title()

    return user_speech.title()


def format_appointment_time(appointment_time) -> str:
    return appointment_time.strftime("%A, %d %B %Y at %I:%M %p")


def format_slot_time(appointment_time) -> str:
    return appointment_time.strftime("%I:%M %p")


def format_available_slots(slots: list) -> str:
    return ", ".join(
        format_slot_time(slot)
        for slot in slots
    )


def find_selected_available_slot(
    user_speech: str,
    available_slots: list
):
    selected_time = parse_appointment_time(user_speech)

    if not selected_time:
        return None

    for slot in available_slots:
        if (
            slot.hour == selected_time.hour
            and slot.minute == selected_time.minute
        ):
            return slot

    return None


def set_call_state(
    call_sid: str,
    caller_number: str,
    state: dict
):
    conversation_state[call_sid] = state

    if caller_number and caller_number != "Unknown":
        conversation_state[caller_number] = state


def get_call_state(
    call_sid: str,
    caller_number: str
) -> dict | None:
    state = conversation_state.get(call_sid)

    if state:
        return state

    if caller_number and caller_number != "Unknown":
        state = conversation_state.get(caller_number)

        if state:
            conversation_state[call_sid] = state
            return state

    return None


def clear_call_state(
    call_sid: str,
    caller_number: str = ""
):
    conversation_state.pop(call_sid, None)

    if caller_number and caller_number != "Unknown":
        conversation_state.pop(caller_number, None)


def safe_start_call_log(
    call_sid: str,
    caller_number: str,
    session: Session
):
    try:
        start_or_get_call_log(
            call_sid,
            caller_number,
            session
        )
    except Exception:
        print("CALL LOG SAVE FAILED")
        traceback.print_exc()
        session.rollback()


def safe_save_user_message(
    call_sid: str,
    user_speech: str,
    session: Session
):
    try:
        save_conversation_message(
            call_sid,
            "USER",
            user_speech,
            session
        )
    except Exception:
        print("USER CONVERSATION SAVE FAILED")
        traceback.print_exc()
        session.rollback()


def safe_generate_transcript(
    call_sid: str,
    session: Session
):
    try:
        generate_call_transcript(
            call_sid,
            session
        )
    except Exception:
        print("CALL TRANSCRIPT GENERATION FAILED")
        traceback.print_exc()
        session.rollback()


@router.get("/voice")
@router.post("/voice")
@router.get("/twilio")
@router.post("/twilio")
async def voice(request: Request):
    form_data = await request.form()
    call_sid = get_form_value(
        form_data,
        "CallSid",
        "unknown-call"
    )
    caller_number = get_form_value(
        form_data,
        "From",
        "Unknown"
    )

    set_call_state(
        call_sid,
        caller_number,
        {
            "step": "detect_department",
            "caller_number": caller_number
        }
    )

    with Session(engine) as session:
        safe_start_call_log(
            call_sid,
            caller_number,
            session
        )
        safe_save_ai_message(
            call_sid,
            "Welcome to Akashwani Hospital. "
            "Please tell me your health issue.",
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

    gather.say(
        "Welcome to Akashwani Hospital. "
        "Please tell me your health issue."
    )

    response.append(gather)

    return Response(
        content=str(response),
        media_type="application/xml"
    )


@router.post("/start-call-log")
async def start_call_log(request: Request):
    form_data = await request.form()
    call_sid = get_form_value(
        form_data,
        "CallSid",
        "unknown-call"
    )
    caller_number = get_form_value(
        form_data,
        "From",
        "Unknown"
    )

    with Session(engine) as session:
        safe_start_call_log(
            call_sid,
            caller_number,
            session
        )

    return {"status": "ok"}


@router.post("/process-speech")
async def process_speech(request: Request):
    form_data = await request.form()
    call_sid = get_form_value(
        form_data,
        "CallSid",
        "unknown-call"
    )
    caller_number = get_form_value(
        form_data,
        "From",
        "Unknown"
    )
    user_speech = get_form_value(
        form_data,
        "SpeechResult"
    )
    with Session(engine) as session:
        safe_start_call_log(
            call_sid,
            caller_number,
            session
        )

        if user_speech:
            safe_save_user_message(
                call_sid,
                user_speech,
                session
            )
        else:
            return gather_response(
                call_sid,
                "Sorry, I could not hear you clearly. "
                "Please tell me your health issue, "
                "for example heart problem or skin allergy.",
                session
            )

        state = get_call_state(
            call_sid,
            caller_number
        )

        if not state:
            state = {
                "step": "detect_department",
                "caller_number": caller_number
            }
            set_call_state(
                call_sid,
                caller_number,
                state
            )

        step = state.get("step")

# Debugging logs
        print("\n" + "=" * 60)
        print("CALL SID:", call_sid)
        print("CURRENT STEP:", step)
        print("USER SAID:", user_speech)
        print("STATE:", state)
        print("=" * 60 + "\n")

        if step == "detect_department":
            department = detect_department(user_speech)

            if not department:
                return gather_response(
                    call_sid,
                    "I could not identify the department. "
                    "Please say heart problem or skin problem.",
                    session
                )

            doctors = find_doctors_by_department(
                department,
                session
            )

            if not doctors:
                return gather_response(
                    call_sid,
                    f"Sorry, no doctor is available in {department} "
                    "right now. Please tell me another health issue.",
                    session
                )

            state["step"] = "choose_doctor"
            state["department"] = department

            doctor_names = ", ".join(
                doctor.name
                for doctor in doctors
            )

            return gather_response(
                call_sid,
                f"You should consult the {department} department. "
                f"Available doctors are: {doctor_names}. "
                "Which doctor would you prefer?",
                session
            )

        if step == "choose_doctor":
            department = state["department"]
            doctors = find_doctors_by_department(
                department,
                session
            )
            doctor = find_doctor_from_speech(
                doctors,
                user_speech
            )

            if not doctor:
                doctor_names = ", ".join(
                    doctor.name
                    for doctor in doctors
                )

                return gather_response(
                    call_sid,
                    "Doctor is unavailable currently. "
                    f"Available doctors are: {doctor_names}. "
                    "Which doctor would you prefer?",
                    session
                )

            state["step"] = "choose_time"
            state["doctor_id"] = str(doctor.id)
            state["doctor_name"] = doctor.name

            return gather_response(
                call_sid,
                "Please tell me your preferred appointment date and time.",
                session
            )

        if step == "collect_patient_name":
            state["patient_name"] = user_speech.title()
            state["step"] = "confirm_patient_name"

            spelled_name = spell_text(state["patient_name"])

            return gather_response(
                call_sid,
                f"I heard your name as {state['patient_name']}. "
                f"I spell it as {spelled_name}. "
                "Is this correct?",
                session
            )

        if step == "confirm_patient_name":

            # Debugging logs
            print("INSIDE confirm_patient_name")
            print("USER RESPONSE:", user_speech)
            print("IS YES:", is_yes(user_speech))
            print("IS NO:", is_no(user_speech))

            if is_yes(user_speech):
                doctor = session.get(
                    Doctor,
                    UUID(state["doctor_id"])
                )

                if not doctor:
                    clear_call_state(
                        call_sid,
                        caller_number
                    )
                    return gather_response(
                        call_sid,
                        "Doctor is unavailable currently. "
                        "Please start again with your health issue.",
                        session
                    )

                create_voice_appointment(
                    patient_name=state["patient_name"],
                    patient_phone=state.get("caller_number", caller_number),
                    doctor_id=doctor.id,
                    doctor_name=doctor.name,
                    appointment_time=state["appointment_time"],
                    session=session
                )

                state["step"] = "appointment_complete"
                safe_generate_transcript(
                    call_sid,
                    session
                )
                clear_call_state(
                    call_sid,
                    caller_number
                )

                return final_response(
                    call_sid,
                    "Your appointment has been booked successfully."
                    "Take care and goodbye!", 
                    session
                )

            if is_no(user_speech):
                state["step"] = "spell_patient_name"

                return gather_response(
                    call_sid,
                    "Please spell your name.",
                    session
                )

            return gather_response(
                call_sid,
                "Please say yes if the spelling is correct, "
                "or no if I should correct it.",
                session
            )

        if step == "spell_patient_name":
            state["patient_name"] = clean_spelled_name(user_speech)

            doctor = session.get(
                Doctor,
                UUID(state["doctor_id"])
            )

            if not doctor:
                clear_call_state(
                    call_sid,
                    caller_number
                )
                return gather_response(
                    call_sid,
                    "Doctor is unavailable currently. "
                    "Please start again with your health issue.",
                    session
                )

            create_voice_appointment(
                patient_name=state["patient_name"],
                patient_phone=state.get("caller_number", caller_number),
                doctor_id=doctor.id,
                doctor_name=doctor.name,
                appointment_time=state["appointment_time"],
                session=session
            )

            state["step"] = "appointment_complete"
            safe_generate_transcript(
                call_sid,
                session
            )
            clear_call_state(
                call_sid,
                caller_number
            )

            return final_response(
                call_sid,
                "Your appointment has been booked successfully.",
                session
            )

        if step == "choose_time":
            appointment_time = parse_appointment_time(
                user_speech
            )

            if not appointment_time:
                return gather_response(
                    call_sid,
                    "Sorry, I could not understand the date and time. "
                    "Please say it like tomorrow at 5 PM.",
                    session
                )

            doctor = session.get(
                Doctor,
                UUID(state["doctor_id"])
            )

            if not doctor:
                clear_call_state(
                    call_sid,
                    caller_number
                )
                return gather_response(
                    call_sid,
                    "Doctor is unavailable currently. "
                    "Would you like another doctor?",
                    session
                )

            if not is_slot_available(
                doctor.id,
                appointment_time,
                session
            ):
                available_slots = get_available_slots(
                    doctor.id,
                    appointment_time.date(),
                    session
                )

                state["step"] = "choose_alternate_slot"
                state["requested_appointment_time"] = appointment_time
                state["available_slots"] = [
                    slot.isoformat()
                    for slot in available_slots
                ]

                if available_slots:
                    return gather_response(
                        call_sid,
                        f"Doctor {doctor.name} is unavailable at "
                        f"{format_slot_time(appointment_time)}. "
                        f"Available slots are: "
                        f"{format_available_slots(available_slots)}. "
                        "Please choose one of these slots.",
                        session
                    )

                return gather_response(
                    call_sid,
                    f"Doctor {doctor.name} is unavailable on "
                    f"{appointment_time.strftime('%A, %d %B %Y')}. "
                    "Please tell another date and time.",
                    session
                )

            state["step"] = "confirm_time_slot"
            state["appointment_time"] = appointment_time

            return gather_response(
                call_sid,
                f"Doctor is available. Do you want to confirm "
                f"your appointment with Doctor {doctor.name} on "
                f"{format_appointment_time(appointment_time)}?",
                session
            )

        if step == "choose_alternate_slot":
            available_slots = [
                datetime.fromisoformat(slot)
                for slot in state.get("available_slots", [])
            ]
            appointment_time = find_selected_available_slot(
                user_speech,
                available_slots
            )

            if not appointment_time:
                return gather_response(
                    call_sid,
                    "Please choose one of the available slots: "
                    f"{format_available_slots(available_slots)}.",
                    session
                )

            doctor = session.get(
                Doctor,
                UUID(state["doctor_id"])
            )

            if not doctor:
                clear_call_state(
                    call_sid,
                    caller_number
                )
                return gather_response(
                    call_sid,
                    "Doctor is unavailable currently. "
                    "Please start again with your health issue.",
                    session
                )

            if not is_slot_available(
                doctor.id,
                appointment_time,
                session
            ):
                available_slots = get_available_slots(
                    doctor.id,
                    appointment_time.date(),
                    session
                )
                state["available_slots"] = [
                    slot.isoformat()
                    for slot in available_slots
                ]

                return gather_response(
                    call_sid,
                    "That slot is no longer available. "
                    f"Available slots are: "
                    f"{format_available_slots(available_slots)}. "
                    "Please choose one of these slots.",
                    session
                )

            state["step"] = "confirm_time_slot"
            state["appointment_time"] = appointment_time

            return gather_response(
                call_sid,
                f"Doctor is available. Do you want to confirm "
                f"your appointment with Doctor {doctor.name} on "
                f"{format_appointment_time(appointment_time)}?",
                session
            )

        if step == "confirm_time_slot":

            # Debugging logs
                print("INSIDE confirm_time_slot")
                print("USER RESPONSE:", user_speech)
                print("IS YES:", is_yes(user_speech))
                print("IS NO:", is_no(user_speech))

                if is_no(user_speech):
                    state["step"] = "choose_time"

                    return gather_response(
                        call_sid,
                        "No problem. Please tell me another date and time.",
                        session
                    )

                if not is_yes(user_speech):
                    return gather_response(
                        call_sid,
                        "Please say yes to confirm this time slot, "
                        "or no to choose another time.",
                        session
                )

                state["step"] = "collect_patient_name"

                return gather_response(
                    call_sid,
                    "Please tell me your full name.",
                    session
                )

        set_call_state(
            call_sid,
            caller_number,
            {
                "step": "detect_department",
                "caller_number": caller_number
            }
        )

        return gather_response(
            call_sid,
            "Please tell me your health issue.",
            session
        )


@router.post("/call-status")
async def call_status(request: Request):
    form_data = await request.form()
    call_sid = get_form_value(
        form_data,
        "CallSid"
    )
    call_status_value = get_form_value(
        form_data,
        "CallStatus",
        "unknown"
    )
    duration = get_form_value(
        form_data,
        "CallDuration"
    )
    duration_seconds = int(duration) if duration.isdigit() else None

    with Session(engine) as session:
        try:
            update_call_status(
                call_sid,
                call_status_value,
                duration_seconds,
                session
            )
        except Exception:
            session.rollback()

        if call_status_value == "completed":
            safe_generate_transcript(
                call_sid,
                session
            )

    return {"status": "ok"}


@router.post("/recording-status")
async def recording_status(request: Request):
    form_data = await request.form()
    call_sid = get_form_value(
        form_data,
        "CallSid"
    )
    recording_url = get_form_value(
        form_data,
        "RecordingUrl"
    )

    if recording_url:
        with Session(engine) as session:
            try:
                save_call_recording(
                    call_sid,
                    recording_url,
                    session
                )
            except Exception:
                session.rollback()

    return {"status": "ok"}
