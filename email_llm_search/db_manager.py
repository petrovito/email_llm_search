import sqlite3
from typing import Optional
from .types import User, ImapAuth, State

class DBManager:
    """Manages an in-memory SQLite database for user and state data."""
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.create_tables()

    def create_tables(self):
        """Initialize the user table."""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE,
                password TEXT,
                last_sync_time TEXT,
                sync_status TEXT
            )
        """)
        self.conn.commit()

    def get_user(self) -> Optional[User]:
        """Retrieve the user data (single user for now)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT email, password, last_sync_time, sync_status FROM user LIMIT 1")
        row = cursor.fetchone()
        if row:
            auth = ImapAuth(email=row[0], password=row[1])
            state = State(last_sync_time=row[2], sync_status=row[3])
            return User(auth=auth, state=state)
        return None

    def set_user(self, user: User):
        """Store or update user data."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO user (id, email, password, last_sync_time, sync_status)
            VALUES (1, ?, ?, ?, ?)
        """, (user.auth.email, user.auth.password, user.state.last_sync_time, user.state.sync_status))
        self.conn.commit()

    def update_state(self, state: State):
        """Update the state information."""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE user SET last_sync_time = ?, sync_status = ?", 
                       (state.last_sync_time, state.sync_status))
        self.conn.commit()