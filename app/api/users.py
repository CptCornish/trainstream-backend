from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..core.database import get_connection
import hashlib
import secrets


router = APIRouter()


def hash_password(password: str) -> str:
    """PBKDF2 password hashing compatible with your desktop app style."""
    salt = secrets.token_bytes(16)
    pw_bytes = password.encode("utf-8")
    digest = hashlib.pbkdf2_hmac("sha256", pw_bytes, salt, 100_000)
    return salt.hex() + ":" + digest.hex()


class User(BaseModel):
    id: int
    first_name: str
    surname: str
    full_name: str
    role: str
    email: Optional[str] = None
    must_change_password: bool


class UserCreate(BaseModel):
    first_name: str
    surname: str
    role: str
    email: Optional[str] = None
    password: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    surname: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    must_change_password: Optional[bool] = None
    password: Optional[str] = None


def row_to_user(row) -> User:
    return User(
        id=row["id"],
        first_name=row["first_name"],
        surname=row["surname"],
        full_name=row["full_name"],
        role=row["role"],
        email=row["email"],
        must_change_password=bool(row["must_change_password"]),
    )


@router.get("/", response_model=List[User])
async def list_users() -> List[User]:
    """Return all users from the existing users table."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                id,
                first_name,
                surname,
                full_name,
                email,
                role,
                must_change_password
            FROM users
            ORDER BY role ASC, full_name ASC
            """
        )
        rows = cur.fetchall()

    return [row_to_user(r) for r in rows]


@router.post("/", response_model=User)
async def create_user(user: UserCreate) -> User:
    """Create a new user in the existing users table."""
    # Build full_name from first + surname
    full_name = f"{user.first_name} {user.surname}".strip()
    hashed = hash_password(user.password)

    with get_connection() as conn:
        cur = conn.cursor()

        # Very light duplicate check on full_name + email combo
        cur.execute(
            "SELECT 1 FROM users WHERE full_name = ? AND email = ?",
            (full_name, user.email or ""),
        )
        if cur.fetchone():
            raise HTTPException(
                status_code=400,
                detail="A user with this name and email already exists",
            )

        cur.execute(
            """
            INSERT INTO users
                (first_name, surname, full_name, email, role,
                 password_hash, must_change_password)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
            (
                user.first_name,
                user.surname,
                full_name,
                user.email or "",
                user.role,
                hashed,
            ),
        )
        user_id = cur.lastrowid
        conn.commit()

        cur.execute(
            """
            SELECT
                id,
                first_name,
                surname,
                full_name,
                email,
                role,
                must_change_password
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        )
        row = cur.fetchone()

    return row_to_user(row)


@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, updates: UserUpdate) -> User:
    """Update an existing user."""
    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                id,
                first_name,
                surname,
                full_name,
                email,
                role,
                must_change_password,
                password_hash
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        )
        row = cur.fetchone()

        if row is None:
            raise HTTPException(status_code=404, detail="User not found")

        current = {
            "first_name": row["first_name"],
            "surname": row["surname"],
            "full_name": row["full_name"],
            "email": row["email"],
            "role": row["role"],
            "must_change_password": bool(row["must_change_password"]),
            "password_hash": row["password_hash"],
        }

        new_first_name = updates.first_name or current["first_name"]
        new_surname = updates.surname or current["surname"]

        if updates.full_name:
            new_full_name = updates.full_name
        else:
            new_full_name = current["full_name"]
            if updates.first_name or updates.surname:
                new_full_name = f"{new_first_name} {new_surname}".strip()

        new_email = (
            updates.email if updates.email is not None else current["email"]
        )
        new_role = updates.role or current["role"]
        new_must_change = (
            updates.must_change_password
            if updates.must_change_password is not None
            else current["must_change_password"]
        )

        new_password_hash = current["password_hash"]
        if updates.password:
            new_password_hash = hash_password(updates.password)

        cur.execute(
            """
            UPDATE users
            SET
                first_name = ?,
                surname = ?,
                full_name = ?,
                email = ?,
                role = ?,
                must_change_password = ?,
                password_hash = ?
            WHERE id = ?
            """,
            (
                new_first_name,
                new_surname,
                new_full_name,
                new_email,
                new_role,
                int(new_must_change),
                new_password_hash,
                user_id,
            ),
        )
        conn.commit()

        cur.execute(
            """
            SELECT
                id,
                first_name,
                surname,
                full_name,
                email,
                role,
                must_change_password
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        )
        updated_row = cur.fetchone()

    return row_to_user(updated_row)
