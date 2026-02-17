"""Multi-turn conversation context manager — condensed format for token efficiency."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat_message import ChatMessage


class ConversationManager:
    """Builds condensed conversation history for AI context."""

    async def get_condensed_history(
        self,
        session_id: str,
        db: AsyncSession,
        max_turns: int = 10,
    ) -> list[dict]:
        """
        Return condensed conversation history.
        Only sends user questions + context_summary (not full AI responses).
        This reduces token usage from ~15K to ~500 tokens.
        """
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(max_turns * 2)
        )
        messages = list(reversed(result.scalars().all()))

        condensed = []
        for msg in messages:
            if msg.role == "user":
                condensed.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant" and msg.context_summary:
                condensed.append({
                    "role": "assistant",
                    "content": f"[context_summary]: {msg.context_summary}",
                })

        return condensed
