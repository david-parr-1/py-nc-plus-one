import psycopg2
from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from db.connection import get_db_connection
from auth.auth import verify_password, create_access_token
from psycopg2.extensions import connection


app = FastAPI()


class CredentialsRequest(BaseModel):
    email: str
    password: str


@app.exception_handler(RequestValidationError)
def handle_request_validation_error(request: Request, exc: RequestValidationError):
    # This exception handler intercepts validations errors which arise from Pydantic data validation
    # of the incoming request. FastAPI rejects these with code 422 by default. This handler
    # intecepts those erros and returns code 400 BAD REQUEST instead.
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"error": exc.errors()})


@app.get("/api/healthcheck")
def healthcheck():
    return {"detail": {"Healthcheck": "Running"}}


@app.get("/api/events")
def get_events(conn: psycopg2.extensions.connection = Depends(get_db_connection)):
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
    return {"events": results_list}


@app.get("/api/events/{event_id}")
def get_event(event_id: int, conn: psycopg2.extensions.connection = Depends(get_db_connection)):
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
            (event_id,)
        )
        row = cur.fetchone()

    if row is None:
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
        "created_at": row[8]
    }
    return {"event": event_data}
    

@app.post("/api/auth/login")
def login_user(payload: CredentialsRequest, conn: psycopg2.extensions.connection = Depends(get_db_connection)):
    # Retrieve the user's hashed password from the users table to enable password
    # verification
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT email, password, id FROM users WHERE email = %s;
            """,
            (payload.email,)
        )
        user = cur.fetchone()
        # Return the same response whether the supplied email address is not in
        # the users table or where the email address is in the users table but
        # the passwords do not match
        if user is None or not verify_password(payload.password, user[1]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        token = create_access_token(user[2])
        return {"token": token}
