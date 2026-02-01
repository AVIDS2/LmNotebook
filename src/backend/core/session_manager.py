
import aiosqlite
import json
import uuid
from typing import List, Dict, Any, Optional
from langchain_core.messages import (
    BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage,
    messages_from_dict, messages_to_dict
)

DB_PATH = "sessions.db"

class SessionManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS session_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT,
                    type TEXT NOT NULL,
                    data JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON session_messages(session_id)")
            await db.commit()

    async def get_history(self, session_id: str) -> List[BaseMessage]:
        """Load full langchain message history for a session."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT data FROM session_messages WHERE session_id = ? ORDER BY id ASC",
                (session_id,)
            )
            rows = await cursor.fetchall()
            
            if not rows:
                return []
            
            # Deserialize JSON back to LangChain Messages
            dicts = [json.loads(row['data']) for row in rows]
            return messages_from_dict(dicts)

    async def add_message(self, session_id: str, message: BaseMessage):
        """Append a message to the session history."""
        # Serialize LangChain message to dict
        msg_dict = messages_to_dict([message])[0]
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO session_messages (session_id, role, content, type, data)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    msg_dict.get("type", "unknown"), # role is implicitly type usually in LC
                    str(message.content),
                    msg_dict["type"],
                    json.dumps(msg_dict)
                )
            )
            await db.commit()

    async def clear_session(self, session_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM session_messages WHERE session_id = ?", (session_id,))
            await db.commit()
