from fastapi import FastAPI
from db.connection import get_db_connection


app = FastAPI()


@app.get("/api/events")
def get_events():
    with get_db_connection() as conn:
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
