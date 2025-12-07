from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core.database import get_connection

router = APIRouter()


# Pydantic models
class CourseTemplateBase(BaseModel):
    name: str
    course_type: Optional[str] = None
    course_title: Optional[str] = None
    provider_type: Optional[str] = None
    default_capacity: Optional[int] = None
    validity_months: Optional[int] = None
    cpd_hours: Optional[float] = None
    default_trainer: Optional[str] = None
    default_venue_id: Optional[int] = None


class CourseTemplateCreate(CourseTemplateBase):
    pass


class CourseTemplateUpdate(BaseModel):
    name: Optional[str] = None
    course_type: Optional[str] = None
    course_title: Optional[str] = None
    provider_type: Optional[str] = None
    default_capacity: Optional[int] = None
    validity_months: Optional[int] = None
    cpd_hours: Optional[float] = None
    default_trainer: Optional[str] = None
    default_venue_id: Optional[int] = None


class CourseTemplateOut(CourseTemplateBase):
    id: int


def row_to_template(row) -> CourseTemplateOut:
    return CourseTemplateOut(
        id=row["id"],
        name=row["name"],
        course_type=row["course_type"],
        # prefer course_title; fall back to default_title if used
        course_title=row["course_title"] or row["default_title"],
        provider_type=row["provider_type"],
        default_capacity=row["default_capacity"],
        validity_months=row["validity_months"],
        cpd_hours=row["cpd_hours"],
        default_trainer=row["default_trainer"],
        default_venue_id=row["default_venue_id"],
    )


@router.get("/", response_model=List[CourseTemplateOut])
async def list_course_templates() -> List[CourseTemplateOut]:
    """Return all course templates."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                id,
                name,
                course_type,
                default_title,
                default_venue_id,
                default_trainer,
                default_capacity,
                course_title,
                provider_type,
                validity_months,
                cpd_hours
            FROM course_templates
            ORDER BY name ASC
            """
        )
        rows = cur.fetchall()

    return [row_to_template(r) for r in rows]


@router.post("/", response_model=CourseTemplateOut)
async def create_course_template(body: CourseTemplateCreate) -> CourseTemplateOut:
    """Create a new course template."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO course_templates
                (
                    name,
                    course_type,
                    default_title,
                    default_venue_id,
                    default_trainer,
                    default_capacity,
                    course_title,
                    provider_type,
                    validity_months,
                    cpd_hours
                )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                body.name,
                body.course_type,
                # default_title – if you ever use it, we mirror course_title by default
                body.course_title,
                body.default_venue_id,
                body.default_trainer,
                body.default_capacity,
                body.course_title,
                body.provider_type,
                body.validity_months,
                body.cpd_hours,
            ),
        )
        template_id = cur.lastrowid
        conn.commit()

        cur.execute(
            """
            SELECT
                id,
                name,
                course_type,
                default_title,
                default_venue_id,
                default_trainer,
                default_capacity,
                course_title,
                provider_type,
                validity_months,
                cpd_hours
            FROM course_templates
            WHERE id = ?
            """,
            (template_id,),
        )
        row = cur.fetchone()

    if row is None:
        raise HTTPException(status_code=500, detail="Failed to fetch created template")

    return row_to_template(row)


@router.put("/{template_id}", response_model=CourseTemplateOut)
async def update_course_template(
    template_id: int, updates: CourseTemplateUpdate
) -> CourseTemplateOut:
    """Update an existing course template."""
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                name,
                course_type,
                default_title,
                default_venue_id,
                default_trainer,
                default_capacity,
                course_title,
                provider_type,
                validity_months,
                cpd_hours
            FROM course_templates
            WHERE id = ?
            """,
            (template_id,),
        )
        row = cur.fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="Template not found")

        current = row_to_template(row)

        new = CourseTemplateBase(
            name=updates.name or current.name,
            course_type=updates.course_type or current.course_type,
            course_title=updates.course_title or current.course_title,
            provider_type=updates.provider_type or current.provider_type,
            default_capacity=(
                updates.default_capacity
                if updates.default_capacity is not None
                else current.default_capacity
            ),
            validity_months=(
                updates.validity_months
                if updates.validity_months is not None
                else current.validity_months
            ),
            cpd_hours=(
                updates.cpd_hours
                if updates.cpd_hours is not None
                else current.cpd_hours
            ),
            default_trainer=(
                updates.default_trainer
                if updates.default_trainer is not None
                else current.default_trainer
            ),
            default_venue_id=(
                updates.default_venue_id
                if updates.default_venue_id is not None
                else current.default_venue_id
            ),
        )

        cur.execute(
            """
            UPDATE course_templates
            SET
                name = ?,
                course_type = ?,
                default_title = ?,
                default_venue_id = ?,
                default_trainer = ?,
                default_capacity = ?,
                course_title = ?,
                provider_type = ?,
                validity_months = ?,
                cpd_hours = ?
            WHERE id = ?
            """,
            (
                new.name,
                new.course_type,
                new.course_title,  # default_title
                new.default_venue_id,
                new.default_trainer,
                new.default_capacity,
                new.course_title,
                new.provider_type,
                new.validity_months,
                new.cpd_hours,
                template_id,
            ),
        )
        conn.commit()

        cur.execute(
            """
            SELECT
                id,
                name,
                course_type,
                default_title,
                default_venue_id,
                default_trainer,
                default_capacity,
                course_title,
                provider_type,
                validity_months,
                cpd_hours
            FROM course_templates
            WHERE id = ?
            """,
            (template_id,),
        )
        updated_row = cur.fetchone()

    return row_to_template(updated_row)
