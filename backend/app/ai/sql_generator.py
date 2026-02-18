"""NL -> SQL translation via Claude API."""

import re
from typing import Optional
from anthropic import AsyncAnthropic
from app.ai.prompts import SYSTEM_PROMPT_SQL_GENERATION
from loguru import logger


class SQLGenerator:
    def __init__(self, client: AsyncAnthropic, model: str = "claude-sonnet-4-20250514"):
        self.client = client
        self.model = model

    async def generate(
        self,
        user_message: str,
        schema_context: str,
        conversation_history: list[dict],
        on_stream: Optional[callable] = None,
    ) -> dict:
        """Generate SQL from natural language question."""
        system_prompt = SYSTEM_PROMPT_SQL_GENERATION.format(
            schema_context=schema_context
        )

        messages = [*conversation_history, {"role": "user", "content": user_message}]

        full_text = ""
        input_tokens = 0
        output_tokens = 0

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                full_text += text
                if on_stream:
                    await on_stream({"phase": "generating_sql", "chunk": text})
            final_message = await stream.get_final_message()
            input_tokens = final_message.usage.input_tokens
            output_tokens = final_message.usage.output_tokens

        sql = self._extract_sql(full_text)
        reasoning = self._extract_reasoning(full_text)

        return {
            "sql": sql,
            "reasoning": reasoning,
            "raw_response": full_text,
            "token_usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        }

    def _extract_sql(self, text: str) -> str:
        """Extract SQL from <sql> tags, ```sql fences, or generic code fences."""
        # Try <sql> tags first
        match = re.search(r"<sql>(.*?)</sql>", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Fallback: try ```sql code fences
        match = re.search(r"```sql\s*(.*?)```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Fallback: try generic code fences with SELECT
        match = re.search(r"```\s*(SELECT.*?)```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return "CANNOT_ANSWER"

    def _extract_reasoning(self, text: str) -> str:
        """Extract reasoning from <reasoning> tags."""
        match = re.search(r"<reasoning>(.*?)</reasoning>", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
