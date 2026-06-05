from sqlmodel import Session, select

from app.models.doctor import Doctor


def find_doctors_by_department(
    department: str,
    session: Session
):

    doctors = session.exec(
        select(Doctor).where(
            Doctor.department.ilike(
                f"%{department}%"
            )
        )
    ).all()

    return doctors

