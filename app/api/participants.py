# app/api/participants.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sqlite3

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect("trainstream.db")
    conn.row_factory = sqlite3.Row
    return conn


router = APIRouter()


class ParticipantBase(BaseModel):
    first_name: str
    surname: str
    contact_number: Optional[str] = None
    email: Optional[str] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None
    joining_sent: bool = False


class ParticipantCreate(ParticipantBase):
    pass


class ParticipantUpdate(BaseModel):
    first_name: Optional[str] = None
    surname: Optional[str] = None
    contact_number: Optional[str] = None
    email: Optional[str] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None
    joining_sent: Optional[bool] = None


class Participant(ParticipantBase):
    id: int
    course_id: int


def row_to_participant(row: sqlite3.Row) -> Participant:
    return Participant(
        id=row["id"],
        course_id=row["course_id"],
        first_name=row["first_name"],
        surname=row["surname"],
        contact_number=row["contact_number"],
        email=row["email"],
        payment_status=row["payment_status"],
        notes=row["notes"],
        joining_sent=bool(row["joining_sent"]),
    )


@router.get("/by-course/{course_id}", response_model=List[Participant])
def list_participants(course_id: int):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, course_id, first_name, surname, contact_number, email,
               payment_status, joining_sent, notes
        FROM participants
        WHERE course_id = ?
        ORDER BY surname, first_name
        """,
        (course_id,),
    )
    rows = cur.fetchall()
    conn.close()
    return [row_to_participant(r) for r in rows]


@router.post("/by-course/{course_id}", response_model=Participant)
def create_participant(course_id: int, payload: ParticipantCreate):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO participants
            (course_id, first_name, surname, contact_number, email,
             payment_status, joining_sent, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            course_id,
            payload.first_name,
            payload.surname,
            payload.contact_number,
            payload.email,
            payload.payment_status,
            1 if payload.joining_sent else 0,
            payload.notes,
        ),
    )
    conn.commit()
    new_id = cur.lastrowid

    cur.execute(
        """
        SELECT id, course_id, first_name, surname, contact_number, email,
               payment_status, joining_sent, notes
        FROM participants
        WHERE id = ?
        """,
        (new_id,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=500, detail="Failed to fetch created participant")

    return row_to_participant(row)


@router.put("/{participant_id}", response_model=Participant)
def update_participant(participant_id: int, payload: ParticipantUpdate):
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM participants WHERE id = ?",
        (participant_id,),
    )
    row = cur.fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Participant not found")

    current = dict(row)

    updated = {
        "first_name": payload.first_name if payload.first_name is not None else current["first_name"],
        "surname": payload.surname if payload.surname is not None else current["surname"],
        "contact_number": payload.contact_number if payload.contact_number is not None else current["contact_number"],
        "email": payload.email if payload.email is not None else current["email"],
        "payment_status": payload.payment_status if payload.payment_status is not None else current["payment_status"],
        "joining_sent": (
            1 if payload.joining_sent else 0
            if payload.joining_sent is not None
            else current["joining_sent"]
        ),
        "notes": payload.notes if payload.notes is not None else current["notes"],
    }

    cur.execute(
        """
        UPDATE participants
        SET first_name = ?, surname = ?, contact_number = ?, email = ?,
            payment_status = ?, joining_sent = ?, notes = ?
        WHERE id = ?
        """,
        (
            updated["first_name"],
            updated["surname"],
            updated["contact_number"],
            updated["email"],
            updated["payment_status"],
            updated["joining_sent"],
            updated["notes"],
            participant_id,
        ),
    )
    conn.commit()

    cur.execute(
        """
        SELECT id, course_id, first_name, surname, contact_number, email,
               payment_status, joining_sent, notes
        FROM participants
        WHERE id = ?
        """,
        (participant_id,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=500, detail="Failed to fetch updated participant")

    return row_to_participant(row)


@router.delete("/{participant_id}")
def delete_participant(participant_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM participants WHERE id = ?", (participant_id,))
    conn.commit()
    conn.close()
    return {"ok": True}
