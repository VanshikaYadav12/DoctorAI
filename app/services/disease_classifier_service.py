import re


DISEASE_DEPARTMENT_MAP = {
    "skin allergy": "Dermatology",
    "skin disease": "Dermatology",
    "skin problem": "Dermatology",
    "rash": "Dermatology",
    "acne": "Dermatology",
    "pimple": "Dermatology",
    "derma": "Dermatology",
    "dermatology": "Dermatology",
    "dermatologist": "Dermatology",

    "heart pain": "Cardiology",
    "heart disease": "Cardiology",
    "heart problem": "Cardiology",
    "chest pain": "Cardiology",
    "cardiac problem": "Cardiology",
    "cardio": "Cardiology",
    "cardiology": "Cardiology",
    "cardiologist": "Cardiology",
    "bp": "Cardiology",
    "blood pressure": "Cardiology",

    "headache": "Neurology",
    "head pain": "Neurology",
    "migraine": "Neurology",
    "brain problem": "Neurology",
    "nerve problem": "Neurology",
    "seizure": "Neurology",
    "dizziness": "Neurology",
    "numbness": "Neurology",
    "stroke": "Neurology",
    "neurology": "Neurology",
    "neurologist": "Neurology",

    "bone pain": "Orthopedics",
    "joint pain": "Orthopedics",
    "knee pain": "Orthopedics",
    "back pain": "Orthopedics",
    "shoulder pain": "Orthopedics",
    "leg pain": "Orthopedics",
    "fracture": "Orthopedics",
    "spine problem": "Orthopedics",
    "orthopedic": "Orthopedics",
    "orthopedics": "Orthopedics",

    "child fever": "Pediatrics",
    "baby fever": "Pediatrics",
    "child cough": "Pediatrics",
    "baby cough": "Pediatrics",
    "my child": "Pediatrics",
    "my baby": "Pediatrics",
    "my kid": "Pediatrics",
    "pediatrics": "Pediatrics",
    "pediatrician": "Pediatrics",
}

DISEASE_SPEECH_HINTS = ", ".join(DISEASE_DEPARTMENT_MAP.keys())


def normalize_speech(user_speech: str) -> str:
    normalized = user_speech.lower()
    normalized = re.sub(r"[^a-z0-9 ]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def detect_department(user_speech: str) -> str | None:
    message = normalize_speech(user_speech)

    for disease, department in DISEASE_DEPARTMENT_MAP.items():
        if disease in message:
            return department

    words = set(message.split())

    for disease, department in DISEASE_DEPARTMENT_MAP.items():
        disease_words = set(disease.split())

        if len(disease_words) == 1 and disease_words.intersection(words):
            return department

    return None
