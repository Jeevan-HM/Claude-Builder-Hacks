"""
Database migration to add tech_stack column to tasks table
Run this once to update the database schema
"""

import os
import sqlite3


def migrate():
    db_path = os.path.join(os.path.dirname(__file__), "project_tracker.db")

    if not os.path.exists(db_path):
        print("Database doesn't exist yet. It will be created with the new schema.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]

        if "tech_stack" not in columns:
            print("Adding tech_stack column to tasks table...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN tech_stack TEXT")
            conn.commit()
            print("✓ Successfully added tech_stack column")
        else:
            print("✓ tech_stack column already exists")

    except Exception as e:
        print(f"✗ Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
