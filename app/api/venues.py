import sqlite3
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


def get_connection() -> sqlite3.Connection:
    """
    Open a connection to the main TrainStream SQLite database.
    """
    conn = sqlite3.connect("trainstream.db")
    conn.row_factory = sqlite3.Row
    return conn


class Venue(BaseModel):
    id: int
    name: str
    address1: str | None = None
    address2: str | None = None
    city: str | None = None
    postcode: str | None = None


@router.get("/", response_model=List[Venue])
async def list_venues() -> list[Venue]:
    """
    Return all venues sorted by name.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, name, address1, address2, city, postcode
        FROM venues
        ORDER BY name ASC
        """
    )
    rows = cur.fetchall()
    conn.close()

    return [Venue(**dict(row)) for row in rows]


@router.get("/{venue_id}", response_model=Venue)
async def get_venue(venue_id: int) -> Venue:
    """
    Return a single venue by ID.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, name, address1, address2, city, postcode
        FROM venues
        WHERE id = ?
        """,
        (venue_id,),
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Venue not found")

    return Venue(**dict(row))
