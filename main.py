from datetime import UTC, datetime
from typing import Annotated, Any

import psycopg2
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, StrictInt, field_validator

from auth.auth import create_access_token, get_user_id, hash_password, verify_password
from db.connection import get_db_connection
from src.logging_config import get_logger

app = FastAPI()


class CredentialsRequest(BaseModel):
    email: str
    password: str


class NewUserRequest(BaseModel):
    name: str
    email: str
    password: str


class NewEvent(BaseModel):
    title: str
    description: str
    starts_at: datetime
    ends_at: datetime
    venue_id: StrictInt

    @field_validator("starts_at", "ends_at", mode="before")
    @classmethod
    def validate_iso8601_datetime(cls, value: object) -> datetime:
        if not isinstance(value, str) or "T" not in value:
            raise ValueError("must be an ISO 8601 datetime string")

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            raise ValueError("must be a valid ISO 8601 datetime string")


logger = get_logger(__name__)


DBConnection = Annotated[psycopg2.extensions.connection, Depends(get_db_connection)]


@app.exception_handler(RequestValidationError)
def handle_request_validation_error(request: Request, exc: RequestValidationError):
    # This exception handler intercepts validations errors which arise from Pydantic data validation
    # of the incoming request. FastAPI rejects these with code 422 by default. This handler
    # intecepts those erros and returns code 400 BAD REQUEST instead.
    errors = [
        {key: value for key, value in error.items() if key not in {"input", "ctx"}}
        for error in exc.errors()
    ]

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content={"error": errors}
    )


@app.get("/api/healthcheck")
def healthcheck():
    return {"detail": {"Healthcheck": "Running"}}


@app.get("/api/events")
def get_events(conn: DBConnection):
    logger.info("Getting all events...")
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                e.id,
                e.title,
                e.starts_at,
                e.ends_at,
                v.name AS location
            FROM events e
            LEFT JOIN venues v on e.venue_id = v.id
            ORDER BY starts_at ASC;
            """
        )
        keys = [desc[0] for desc in cur.description]
        rows = cur.fetchall()

    results_list = [dict(zip(keys, row)) for row in rows]
    logger.info(f"{len(rows)} events returned successfully.")
    return {"events": results_list}


@app.get("/api/events/{event_id}")
def get_event(event_id: int, conn: DBConnection):
    logger.info(f"Retrieving event id {event_id}...")
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                e.id,
                e.title,
                e.description,
                e.starts_at,
                e.ends_at,
                v.name AS location,
                v.address,
                v.capacity,
                e.created_at
            FROM events e
            LEFT JOIN venues v on e.venue_id = v.id
            WHERE e.id = %s;
            """,
            (event_id,),
        )
        row = cur.fetchone()

    if row is None:
        logger.warning(f"Event id {event_id} could not be found.")
        raise HTTPException(status_code=404, detail="Event not found")

    event_data = {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "starts_at": row[3],
        "ends_at": row[4],
        "location": row[5],
        "address": row[6],
        "capacity": row[7],
        "created_at": row[8],
    }
    logger.info(f"Event id {event_id} returned successfully.")
    return {"event": event_data}


@app.post("/api/auth/login")
def login_user(
    payload: CredentialsRequest,
    conn: DBConnection,
):
    # Retrieve the user's hashed password from the users table to enable password
    # verification
    logger.info(f"Logging in user {payload.email}...")
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT email, password, id FROM users WHERE email = %s;
            """,
            (payload.email,),
        )
        user = cur.fetchone()
        # Return the same response whether the supplied email address is not in
        # the users table or where the email address is in the users table but
        # the passwords do not match
        if user is None or not verify_password(payload.password, user[1]):
            logger.warning(
                f"User {payload.email} could not be logged in: user does not "
                f"exist or password is invalid."
            )
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token(user[2])
        logger.info(f"User {payload.email} logged in successfully.")
        return {"token": token}


@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(
    payload: NewUserRequest,
    conn: DBConnection,
):
    logger.info(f"Attempting to register new user {payload.email}...")
    hashed_password = hash_password(payload.password)
    created_at = datetime.now(UTC)
    with conn.cursor() as cur:
        query = """
            INSERT INTO users (name, email, password, created_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            RETURNING id, name, email, created_at;
            """

        cur.execute(query, (payload.name, payload.email, hashed_password, created_at))

        created_user = cur.fetchone()

    conn.commit()

    if created_user is None:
        logger.warning(f"User {payload.email} already exists.")
        raise HTTPException(status_code=409, detail="Email already registered")

    logger.info(f"Successfully register new user {payload.email}.")
    return {
        "user": {
            "id": created_user[0],
            "name": created_user[1],
            "email": created_user[2],
            "created_at": created_user[3],
        }
    }


@app.post("/api/events/{event_id}/rsvp", status_code=status.HTTP_201_CREATED)
def add_rsvp(
    conn: DBConnection,
    event_id: int,
    user: int = Depends(get_user_id),
) -> dict[str, dict[str, Any]]:
    logger.info(f"Attempting to verify existence of event_id {event_id}...")
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM events WHERE id = %s;", (event_id,))

        if cur.fetchone() is None:
            logger.error(f"event_id {event_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )

        logger.info(f"event_id {event_id} found successfully.")

        logger.info(
            f"Attempting to write RSVP for user: {user} and event: {event_id} to "
            f"database..."
        )
        query = """
        INSERT INTO rsvps (attendee_id, event_id)
        VALUES(%s, %s)
        ON CONFLICT (attendee_id, event_id) DO NOTHING
        RETURNING id, created_at;
        """

        cur.execute(query, (user, event_id))
        rsvp_attributes = cur.fetchone()

        conn.commit()

    if rsvp_attributes is None:
        logger.warning(f"RSVP already exists for user {user} and event {event_id}.")
        raise HTTPException(status_code=409, detail="RSVP already registered")

    logger.info(f"Successfully created RSVP for user {user} for event {event_id}.")
    payload = {
        "rsvp": {
            "id": rsvp_attributes[0],
            "attendee_id": user,
            "event_id": event_id,
            "created_at": rsvp_attributes[1],
        }
    }

    return payload


@app.delete("/api/events/{event_id}/rsvp/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_rsvp(conn: DBConnection, event_id: int, user: int = Depends(get_user_id)):
    logger.info(
        f"Attempting to verify existence of RSVP for attendee_id: {user} and "
        f"event_id: {event_id}..."
    )
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id FROM rsvps WHERE attendee_id = %s AND event_id = %s;",
            (user, event_id),
        )

        result = cur.fetchone()

        if result is None:
            logger.error(
                f"RSVP not found for attendee_id: {user} and event_id: {event_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="RSVP not found"
            )

        rsvp_id = result[0]
        logger.info(
            f"RSVP id: {rsvp_id} found for attendee_id: {user} and event_id: {event_id}"
        )

        logger.info(
            f"Attempting to delete RSVP id: {rsvp_id} for attendee_id: {user} and "
            f"event_id: {event_id}"
        )

        cur.execute("DELETE FROM rsvps WHERE id = %s;", (rsvp_id,))

        conn.commit()

    logger.info(
        f"Successfully deleted RSVP id: {rsvp_id} for attendee_id: {user} and "
        f"event_id: {event_id}"
    )


@app.post("/api/events", status_code=status.HTTP_201_CREATED)
def create_event(
    conn: DBConnection,
    payload: NewEvent,
    user: int = Depends(get_user_id),
):
    # Verify that the venue_id in the JSON data exists in the venues table before
    # going any further.
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM venues WHERE id = %s;", (payload.venue_id,))

        if cur.fetchone is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="venue_id not found"
            )

        query = """
        INSERT INTO events (title, description, starts_at, ends_at, organiser_id, venue_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, title, description, starts_at, ends_at, venue_id, organiser_id, created_at;
        """
        cur.execute(
            query,
            (
                payload.title,
                payload.description,
                payload.starts_at,
                payload.ends_at,
                user,
                payload.venue_id,
            ),
        )
        new_event = cur.fetchone() if cur.fetchone is not None else None
        if new_event is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error",
            )
    conn.commit()

    return {
        "event": {
            "id": new_event[0],
            "title": new_event[1],
            "description": new_event[2],
            "starts_at": new_event[3],
            "ends_at": new_event[4],
            "venue_id": new_event[5],
            "organiser_id": new_event[6],
            "created_at": new_event[7],
        }
    }
