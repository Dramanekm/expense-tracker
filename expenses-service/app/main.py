import os
from datetime import date

import psycopg
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="expenses-service")


class Expense(BaseModel):
    label: str
    amount: float
    category: str
    date: date


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


def to_dict(row):
    return {
        "id": row[0],
        "label": row[1],
        "amount": float(row[2]),
        "category": row[3],
        "date": row[4],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/expenses")
def list_expenses():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, label, amount, category, date FROM expenses ORDER BY date DESC"
        ).fetchall()
    result = []
    for row in rows:
        result.append(to_dict(row))
    return result


@app.post("/expenses", status_code=201)
def create_expense(expense: Expense):
    with get_connection() as conn:
        row = conn.execute(
            "INSERT INTO expenses (label, amount, category, date) VALUES (%s, %s, %s, %s) "
            "RETURNING id, label, amount, category, date",
            (expense.label, expense.amount, expense.category, expense.date),
        ).fetchone()
    return to_dict(row)


@app.put("/expenses/{expense_id}")
def update_expense(expense_id: int, expense: Expense):
    with get_connection() as conn:
        row = conn.execute(
            "UPDATE expenses SET label = %s, amount = %s, category = %s, date = %s "
            "WHERE id = %s RETURNING id, label, amount, category, date",
            (expense.label, expense.amount, expense.category, expense.date, expense_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Dépense introuvable")
    return to_dict(row)


@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "DELETE FROM expenses WHERE id = %s RETURNING id", (expense_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Dépense introuvable")
