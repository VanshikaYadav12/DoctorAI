import re

from datetime import datetime, timedelta , time

from sqlmodel import Session, select

from app.models.appointments import Appointment
from app.models.doctor import Doctor


NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
}


def find_doctors_by_department(
    department: str,
    session: Session
) -> list[Doctor]:
    return session.exec(
        select(Doctor).where(
            Doctor.department.ilike(f"%{department}%")
        )
    ).all()


def normalize_name(name: str) -> str:
    normalized = name.lower()
    normalized = re.sub(r"\b(dr|doctor)\b\.?", "", normalized)
    normalized = re.sub(r"[^a-z0-9 ]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def find_doctor_from_speech(
    doctors: list[Doctor],
    spoken_name: str
) -> Doctor | None:
    spoken = normalize_name(spoken_name)
    spoken_tokens = set(spoken.split())

    for doctor in doctors:
        doctor_name = normalize_name(doctor.name)
        doctor_tokens = set(doctor_name.split())

        if spoken in doctor_name or doctor_name in spoken:
            return doctor

        if doctor_tokens and doctor_tokens.issubset(spoken_tokens):
            return doctor

        if len(doctor_tokens.intersection(spoken_tokens)) >= 2:
            return doctor

    return None


def parse_appointment_time(user_speech: str) -> datetime | None:
    speech = (
        user_speech.lower()
        .replace("p m", "pm")
        .replace("a m", "am")
    )
    now = datetime.now()

    if "tomorrow" in speech:
        appointment_date = now.date() + timedelta(days=1)
    elif "today" in speech:
        appointment_date = now.date()
    else:
        appointment_date = now.date()

    numeric_time = re.search(
        r"\b(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)?\b",
        speech
    )

    if numeric_time:
        hour = int(numeric_time.group(1))
        minute = int(numeric_time.group(2) or 0)
        meridiem = numeric_time.group(3)
    else:
        hour = None
        minute = 0
        meridiem = None

        for word, value in NUMBER_WORDS.items():
            spoken_time = re.search(
                rf"\b{word}\s*(a\.?m\.?|p\.?m\.?)?\b",
                speech
            )

            if spoken_time:
                hour = value
                meridiem = spoken_time.group(1)
                break

        if hour is None:
            return None

    if hour > 23 or minute > 59:
        return None

    if meridiem:
        meridiem = meridiem.replace(".", "")

        if meridiem == "pm" and hour != 12:
            hour += 12
        elif meridiem == "am" and hour == 12:
            hour = 0

    return datetime.combine(
        appointment_date,
        datetime.min.time()
    ).replace(
        hour=hour,
        minute=minute
    )


def is_slot_available(
    doctor_id,
    appointment_time: datetime,
    session: Session
) -> bool:
    slot_end_time = appointment_time + timedelta(minutes=30)

    existing_appointment = session.exec(
        select(Appointment).where(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_time >= appointment_time,
            Appointment.appointment_time < slot_end_time,
            Appointment.status != "cancelled"
        )
    ).first()

    return existing_appointment is None


def create_voice_appointment(
    patient_name: str,
    patient_phone: str,
    doctor_id,
    doctor_name: str,
    appointment_time: datetime,
    session: Session
) -> Appointment:
    appointment = Appointment(
        patient_name=patient_name,
        patient_phone=patient_phone,
        appointment_time=appointment_time,
        doctor_id=doctor_id,
        doctor_name=doctor_name,
        notes="Booked through Twilio voice assistant."
    )

    session.add(appointment)
    session.commit()
    session.refresh(appointment)

    return appointment


def get_available_slots(
    doctor_id,
    appointment_date,
    session: Session
):

    available_slots = []

    working_hours = [
        10, 11, 12, 13, 14, 15, 16, 17
    ]

    for hour in working_hours:

        slot_time = datetime.combine(
            appointment_date,
            time(hour=hour)
        )

        if is_slot_available(
            doctor_id,
            slot_time,
            session
        ):
            available_slots.append(slot_time)

    return available_slots