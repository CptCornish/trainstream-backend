# app/api/courses.py

from __future__ import annotations

import sqlite3
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

router = APIRouter()


def get_connection() -> sqlite3.Connection:
    """
    Simple helper to open a connection to trainstream.db.

    Uses the current working directory, which is the backend folder
    when you run `uvicorn app.main:app --reload`.
    """
    conn = sqlite3.connect("trainstream.db")
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------------
# Pydantic models
# -----------------------------

class Course(BaseModel):
    id: int
    title: str
    code: str
    start_date: str
    end_date: Optional[str]
    trainer_name: str
    venue_name: str
    status: str


class CourseCreate(BaseModel):
    """
    Payload for creating a new course from a template.
    """
    template_id: int
    course_date: date
    venue_id: Optional[int] = None
    trainer: str = ""
    capacity: Optional[int] = None
    status: str = "Planned"


# -----------------------------
# Helper functions
# -----------------------------

def _get_template_shortname(template_name: str) -> str:
    """
    Mirror the desktop helper:

    "FREC 3 – Qualsafe" -> "FREC3QUALSAFE"
    """
    clean = "".join(ch for ch in template_name if ch.isalnum())
    return clean.upper()


def _get_next_cohort_number(cur: sqlite3.Cursor, template_id: int, year: str) -> int:
    """
    Look at existing course_ref values for this template + year and
    return the next cohort number.

    Existing pattern: SHORTNAME-YEAR-XXX
    """
    cur.execute(
        "SELECT course_ref FROM courses WHERE template_id = ? AND course_ref LIKE ?",
        (template_id, f"%-{year}-%"),
    )
    rows = cur.fetchall()
    numbers: list[int] = []

    for (course_ref,) in rows:
        if not course_ref:
            continue
        parts = str(course_ref).split("-")
        if len(parts) < 3:
            continue
        try:
            cohort_str = parts[-1]
            numbers.append(int(cohort_str))
        except Exception:
            # Ignore malformed refs
            pass

    return max(numbers) + 1 if numbers else 1


def _row_to_course(row: sqlite3.Row) -> Course:
    return Course(
        id=row["id"],
        title=row["title"],
        code=row["code"],
        start_date=row["start_date"],
        end_date=row["end_date"],
        trainer_name=row["trainer_name"],
        venue_name=row["venue_name"],
        status=row["status"],
    )


# -----------------------------
# Routes
# -----------------------------

@router.get("/", response_model=List[Course])
def list_courses() -> List[Course]:
    """
    Return all courses, joined to venues, in the shape the frontend expects.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            c.id,
            c.course_title AS title,
            c.course_ref AS code,
            c.course_date AS start_date,
            c.course_date AS end_date,
            COALESCE(c.trainer, '') AS trainer_name,
            COALESCE(v.name, '') AS venue_name,
            COALESCE(c.status, 'Planned') AS status
        FROM courses c
        LEFT JOIN venues v ON v.id = c.venue_id
        ORDER BY c.course_date DESC, c.id DESC
        """
    )
    rows = cur.fetchall()
    conn.close()
    return [_row_to_course(r) for r in rows]


@router.get("/{course_id}", response_model=Course)
def get_course(course_id: int) -> Course:
    """
    Fetch a single course by ID.
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            c.id,
            c.course_title AS title,
            c.course_ref AS code,
            c.course_date AS start_date,
            c.course_date AS end_date,
            COALESCE(c.trainer, '') AS trainer_name,
            COALESCE(v.name, '') AS venue_name,
            COALESCE(c.status, 'Planned') AS status
        FROM courses c
        LEFT JOIN venues v ON v.id = c.venue_id
        WHERE c.id = ?
        """,
        (course_id,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Course not found")

    return _row_to_course(row)


@router.post("/", response_model=Course)
def create_course(payload: CourseCreate) -> Course:
    """
    Create a new course based on a template + date + venue, etc.
    Uses the same course_ref pattern as the desktop app:
        SHORTNAME-YEAR-XXX
    """
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1) Look up the template
    cur.execute(
        """
        SELECT id, name, course_title, default_capacity
        FROM course_templates
        WHERE id = ?
        """,
        (payload.template_id,),
    )
    tmpl = cur.fetchone()
    if tmpl is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Template not found")

    template_name = tmpl["name"]
    course_title = tmpl["course_title"] or template_name
    default_capacity = tmpl["default_capacity"] or 12

    # 2) Build course_ref
    year_str = payload.course_date.strftime("%Y")
    shortname = _get_template_shortname(template_name)
    next_cohort = _get_next_cohort_number(cur, payload.template_id, year_str)
    course_ref = f"{shortname}-{year_str}-{next_cohort:03d}"

    # 3) Decide capacity & status
    capacity = payload.capacity if payload.capacity and payload.capacity > 0 else default_capacity
    status = payload.status or "Planned"

    # 4) Insert into courses table
    course_date_str = payload.course_date.strftime("%Y-%m-%d")

    cur.execute(
        """
        INSERT INTO courses
            (course_ref, course_date, template_id, course_title,
             trainer, venue_id, capacity, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            course_ref,
            course_date_str,
            payload.template_id,
            course_title,
            payload.trainer,
            payload.venue_id,
            capacity,
            status,
        ),
    )
    new_id = cur.lastrowid
    conn.commit()

    # 5) Read it back in the same shape as list/get
    cur.execute(
        """
        SELECT
            c.id,
            c.course_title AS title,
            c.course_ref AS code,
            c.course_date AS start_date,
            c.course_date AS end_date,
            COALESCE(c.trainer, '') AS trainer_name,
            COALESCE(v.name, '') AS venue_name,
            COALESCE(c.status, 'Planned') AS status
        FROM courses c
        LEFT JOIN venues v ON v.id = c.venue_id
        WHERE c.id = ?
        """,
        (new_id,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        # Extremely unlikely, but be defensive
        raise HTTPException(status_code=500, detail="Failed to load created course")

    return _row_to_course(row)
