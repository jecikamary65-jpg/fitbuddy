"""
Database abstraction layer for FitBuddy using SQLite.
Handles table creation, transactions, and CRUD operations cleanly without exposing raw SQL in routes.
"""

import sqlite3
import os
import json
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

logger = logging.getLogger("fitbuddy.database")

# Default database path can be overridden by environment variable
DB_PATH = os.getenv("FITBUDDY_DB_PATH", os.path.join(os.path.dirname(__file__), "fitbuddy.db"))


@contextmanager
def get_db_connection():
    """
    Context manager for SQLite database connections.
    Ensures foreign keys are enabled and rows are returned as dictionaries.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.error(f"Database error occurred: {exc}")
        raise
    finally:
        conn.close()


def init_db():
    """
    Initializes the SQLite database tables if they do not exist.
    """
    logger.info(f"Initializing database at: {DB_PATH}")
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Users table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                weight REAL NOT NULL,
                goal TEXT NOT NULL,
                intensity TEXT NOT NULL,
                experience_level TEXT NOT NULL,
                preferences TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Workout Plans table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS workout_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_data TEXT NOT NULL,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )

        # Nutrition Tips table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS nutrition_tips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                goal TEXT NOT NULL,
                tip TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            )
            """
        )
        logger.info("Database tables verified/created successfully.")


# ------------------ User Operations ------------------ #

def create_user(
    name: str,
    age: int,
    weight: float,
    goal: str,
    intensity: str,
    experience_level: str,
    preferences: Optional[str] = None,
) -> int:
    """Inserts a new user and returns their generated ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (name, age, weight, goal, intensity, experience_level, preferences)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (name.strip(), age, weight, goal, intensity, experience_level, (preferences or "").strip()),
        )
        return cursor.lastrowid


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves a user dictionary by their ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


# ------------------ Workout Plan Operations ------------------ #

def save_workout_plan(user_id: int, plan_data: Dict[str, Any], feedback: Optional[str] = None) -> int:
    """Saves a newly generated workout plan to the database."""
    json_data = json.dumps(plan_data, ensure_ascii=False)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO workout_plans (user_id, plan_data, feedback, created_at, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (user_id, json_data, feedback),
        )
        return cursor.lastrowid


def update_workout_plan(plan_id: int, plan_data: Dict[str, Any], feedback: str) -> bool:
    """Updates an existing workout plan with new data and feedback record."""
    json_data = json.dumps(plan_data, ensure_ascii=False)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE workout_plans
            SET plan_data = ?, feedback = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (json_data, feedback, plan_id),
        )
        return cursor.rowcount > 0


def get_latest_plan_by_user(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetches the most recently created or updated workout plan for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT wp.*, u.name as user_name, u.goal, u.intensity, u.experience_level, u.age, u.weight
            FROM workout_plans wp
            JOIN users u ON wp.user_id = u.id
            WHERE wp.user_id = ?
            ORDER BY wp.updated_at DESC, wp.id DESC
            LIMIT 1
            """,
            (user_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        data = dict(row)
        try:
            data["plan_data"] = json.loads(data["plan_data"])
        except json.JSONDecodeError:
            pass
        return data


def get_plan_by_id(plan_id: int) -> Optional[Dict[str, Any]]:
    """Fetches a workout plan by plan ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT wp.*, u.name as user_name, u.goal, u.intensity, u.experience_level, u.age, u.weight
            FROM workout_plans wp
            JOIN users u ON wp.user_id = u.id
            WHERE wp.id = ?
            """,
            (plan_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        data = dict(row)
        try:
            data["plan_data"] = json.loads(data["plan_data"])
        except json.JSONDecodeError:
            pass
        return data


# ------------------ Nutrition Tip Operations ------------------ #

def save_nutrition_tip(user_id: Optional[int], goal: str, tip: str) -> int:
    """Saves a generated nutrition or recovery tip."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO nutrition_tips (user_id, goal, tip)
            VALUES (?, ?, ?)
            """,
            (user_id, goal, tip),
        )
        return cursor.lastrowid


def get_recent_tips_by_user(user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
    """Retrieves recent nutrition tips generated for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM nutrition_tips
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        return [dict(row) for row in cursor.fetchall()]
