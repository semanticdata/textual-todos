"""Database connection and initialization."""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import DB_PATH, DEFAULT_PROJECT, SchemaVersion


class DatabaseConnection:
    """Handles database connections and schema management."""

    def __init__(self, path: str = DB_PATH):
        """Initialize database connection.

        Args:
            path: Path to the SQLite database file
        """
        self.path = path
        self._ensure_db_directory()
        self._init_schema()

    def _ensure_db_directory(self) -> None:
        """Ensure the directory for the database file exists."""
        db_path = Path(self.path)
        if db_path.parent:
            db_path.parent.mkdir(parents=True, exist_ok=True)

    def _init_schema(self) -> None:
        """Initialize database schema if it doesn't exist."""
        with self.get_connection() as conn:
            # Create projects table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL
                )
            """)

            # Create tasks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    completed BOOLEAN NOT NULL DEFAULT 0,
                    priority TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    modified_at TEXT NOT NULL,
                    due_date TEXT,
                    project_id INTEGER NOT NULL,
                    FOREIGN KEY(project_id) REFERENCES projects(id)
                )
            """)

            # Create schema version table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY
                )
            """)

            # Check current schema version
            cursor = conn.execute("SELECT version FROM schema_version LIMIT 1")
            current_version = cursor.fetchone()

            if current_version is None:
                # New database, set initial version
                conn.execute(
                    "INSERT INTO schema_version (version) VALUES (?)",
                    (SchemaVersion.CURRENT,),
                )
                # Create default project
                conn.execute(
                    "INSERT OR IGNORE INTO projects (name) VALUES (?)",
                    (DEFAULT_PROJECT,),
                )
            else:
                # Database exists, run migrations if needed
                self._run_migrations(conn, current_version["version"])

    def _run_migrations(self, conn: sqlite3.Connection, current_version: int) -> None:
        """Run database migrations if needed.

        Args:
            conn: Database connection
            current_version: Current schema version
        """
        # Example migration (add more as needed):
        # if current_version < 2:
        #     # Migration code for version 2
        #     pass
        #
        # Update schema version
        conn.execute("UPDATE schema_version SET version = ?", (SchemaVersion.CURRENT,))

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory set to return dicts.

        Returns:
            sqlite3.Connection: Database connection
        """

        def dict_factory(cursor, row):
            return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

        conn = sqlite3.connect(self.path)
        conn.row_factory = dict_factory
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def execute(self, query: str, params: Tuple[Any, ...] = ()) -> sqlite3.Cursor:
        """Execute a query and return the cursor.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            sqlite3.Cursor: Cursor with results
        """
        with self.get_connection() as conn:
            return conn.execute(query, params)

    def fetch_all(self, query: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
        """Execute a query and fetch all results.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            List of result rows as dictionaries
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def fetch_one(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[Dict[str, Any]]:
        """Execute a query and fetch one result.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Single result row as dictionary or None if no results
        """
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()


# Global database connection instance
db = DatabaseConnection()
