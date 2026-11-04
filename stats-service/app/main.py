import os

import psycopg
from fastapi import FastAPI

app = FastAPI(title="stats-service")


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "expenses"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.environ["DB_PASSWORD"],
    )


@app.on_event("startup")
def create_table():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id SERIAL PRIMARY KEY,
                label TEXT NOT NULL,
                amount NUMERIC(10, 2) NOT NULL,
                category TEXT NOT NULL,
                date DATE NOT NULL
            )
            """
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats/total")
def total():
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM expenses"
        ).fetchone()
    return {"total": float(row[0]), "count": row[1]}


@app.get("/stats/by-category")
def by_category():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT category, SUM(amount) FROM expenses GROUP BY category ORDER BY category"
        ).fetchall()
    result = []
    for row in rows:
        result.append({"category": row[0], "total": float(row[1])})
    return result


@app.get("/stats/by-month")
def by_month():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT TO_CHAR(date, 'YYYY-MM') AS month, SUM(amount) FROM expenses "
            "GROUP BY month ORDER BY month"
        ).fetchall()
    result = []
    for row in rows:
        result.append({"month": row[0], "total": float(row[1])})
    return result
