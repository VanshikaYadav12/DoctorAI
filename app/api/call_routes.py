import os

from datetime import datetime

from fastapi import APIRouter
from fastapi import Request
from fastapi.responses import Response

from sqlmodel import Session
from sqlmodel import select

from groq import Groq

from twilio.twiml.voice_response import (
    VoiceResponse,
    Gather
)

from app.database.db import engine

from app.models.appointments import Appointment
from app.models.doctor import Doctor

from app.services.appointment import (
    find_doctors_by_department
)

router = APIRouter()

conversation_state = {}

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


@router.post("/voice")
async def voice():

    response = VoiceResponse()

    gather = Gather(
        input="speech",
        action="https://unworshipped-fearfully-chanell.ngrok-free.dev/process-speech",
        method="POST"
    )

    gather.say(
        "Hello. Welcome to Akashwani Hospital. "
        "How can I help you today?"
    )

    response.append(gather)

    return Response(
        content=str(response),
        media_type="application/xml"
    )


@router.post("/process-speech")
async def process_speech(request: Request):

    form_data = await request.form()

    call_sid = form_data.get("CallSid")

    user_speech = form_data.get(
        "SpeechResult",
        ""
    ).strip()

    print("\n" + "=" * 60)
    print("CALL SID:", call_sid)
    print("USER SAID:", repr(user_speech))
    print("CURRENT STATE:", conversation_state)
    print("=" * 60 + "\n")

    user_message = user_speech.lower()

    with Session(engine) as session:

        # ====================================
        # CARDIOLOGY FLOW
        # ====================================
        if any(word in user_message for word in [
            "cardio",
            "heart",
            "heart doctor",
            "cardiologist",
            "chest pain"
        ]):

            doctors = find_doctors_by_department(
                "Cardiology",
                session
            )

            if doctors:

                conversation_state[call_sid] = {
                  "step": "choose_doctor",
                "department": "Cardiology"
                }

                print(
                    "STATE CREATED:",
                    conversation_state[call_sid]
                ) 

                doctor_names = ", ".join(
                    [
                        doctor.name
                        for doctor in doctors
                    ]
                )

                answer = (
                    f"We have these cardiologists available: "
                    f"{doctor_names}. "
                    f"Which doctor would you prefer?"
                )

            else:

                answer = (
                    "Sorry, no cardiologist "
                    "is available right now."
                )

        # ====================================
        # DERMATOLOGY FLOW
        # ====================================
        elif any(word in user_message for word in [
            "skin",
            "pimple",
            "acne",
            "rash",
            "allergy",
            "derma",
            "dermatologist",
            "skin doctor"
        ]):

            doctors = find_doctors_by_department(
                "Dermatology",
                session
            )

            if doctors:

                conversation_state[call_sid] = {
                  "step": "choose_doctor",
                "department": "Dermatology"
                }

                print(
                    "STATE CREATED:",
                    conversation_state[call_sid]
                ) 


                doctor_names = ", ".join(
                    [
                        doctor.name
                        for doctor in doctors
                    ]
                )

                answer = (
                    f"We have these dermatologists available: "
                    f"{doctor_names}. "
                    f"Which doctor would you prefer?"
                )

            else:

                answer = (
                    "Sorry, no dermatologist "
                    "is available right now."
                )

        # ====================================
        # CONVERSATION STATE FLOW
        # ====================================
        elif call_sid in conversation_state:

            state = conversation_state[call_sid]

            print(
                "STATE FOUND:",
                state
            )

            # STEP 1 -> USER SELECTS DOCTOR
            if "doctor_selected" not in state:

                state["doctor_selected"] = user_speech

                answer = (
                    "Please tell me your preferred "
                    "appointment date and time."
                )

            # STEP 2 -> USER PROVIDES TIME
            elif "appointment_time" not in state:

                state["appointment_time"] = user_speech

                doctor = session.exec(
                    select(Doctor).where(
                        Doctor.name.ilike(
                            f"%{state['doctor_selected']}%"
                        )
                    )
                ).first()

                if doctor:

                    appointment = Appointment(
                        patient_name="Voice Caller",
                        patient_phone="Unknown",
                        appointment_time=datetime.utcnow(),
                        notes=(
                            f"Requested time: "
                            f"{state['appointment_time']}"
                        ),
                        doctor_id=doctor.id
                    )

                    session.add(appointment)
                    session.commit()

                    answer = (
                        f"Your appointment request "
                        f"has been booked with "
                        f"Doctor {doctor.name}. "
                        f"Thank you for calling Akashwani Hospital."
                    )

                else:

                    answer = (
                        "Sorry, I could not "
                        "find that doctor."
                    )

                conversation_state.pop(call_sid)

        # ====================================
        # FALLBACK AI RESPONSE
        # ====================================
        else:

            ai_response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful hospital "
                            "AI receptionist."
                        )
                    },
                    {
                        "role": "user",
                        "content": user_speech
                    }
                ]
            )

            answer = (
                ai_response
                .choices[0]
                .message
                .content
            )

    response = VoiceResponse()

    gather = Gather(
        input="speech",
        action="https://unworshipped-fearfully-chanell.ngrok-free.dev/process-speech",
        method="POST"
    )

    gather.say(answer)

    response.append(gather)

    return Response(
        content=str(response),
        media_type="application/xml"
    )
