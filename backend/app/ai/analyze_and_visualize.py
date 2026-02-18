"""Merged insight + chart recommendation -- single Claude API call."""

import json
from typing import Optional
from anthropic import AsyncAnthropic
from app.ai.prompts import SYSTEM_PROMPT_ANALYZE_AND_VISUALIZE
from loguru import logger


class AnalyzeAndVisualize:
    def __init__(self, client: AsyncAnthropic, model: str = "claude-sonnet-4-20250514"):
        self.client = client
        self.model = model

    async def analyze(
        self,
        user_message: str,
        sql: str,
        result_data: dict,
        on_stream: Optional[callable] = None,
    ) -> dict:
        """Analyze query results and recommend visualization."""
        # Prepare result preview (limit to 50 rows for prompt)
        columns = result_data.get("columns", [])
        rows = result_data.get("rows", [])[:50]
        row_count = result_data.get("row_count", len(rows))

        # Format result preview as table
        result_preview = self._format_result_preview(columns, rows)

        system_prompt = SYSTEM_PROMPT_ANALYZE_AND_VISUALIZE.format(
            user_message=user_message,
            sql=sql,
            row_count=row_count,
            columns=", ".join(columns),
            result_preview=result_preview,
        )

        full_text = ""
        input_tokens = 0
        output_tokens = 0

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=1500,
            system="You are DataMind, an AI business analyst.",
            messages=[{"role": "user", "content": system_prompt}],
        ) as stream:
            async for text in stream.text_stream:
                full_text += text
                if on_stream:
                    await on_stream({"phase": "analyzing", "chunk": text})
            final_message = await stream.get_final_message()
            input_tokens = final_message.usage.input_tokens
            output_tokens = final_message.usage.output_tokens

        token_usage = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

        # Strip markdown code fences before parsing JSON
        cleaned = full_text.strip()
        if cleaned.startswith("```"):
            first_newline = cleaned.find("\n")
            if first_newline != -1:
                cleaned = cleaned[first_newline + 1:]
            else:
                cleaned = cleaned[3:]
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3].rstrip()

        try:
            parsed = json.loads(cleaned)
            return {
                "insight": parsed.get("content", "Analysis complete."),
                "context_summary": parsed.get("context_summary", ""),
                "chart_config": parsed.get("chart_config", {"chart_type": "table", "title": "Results"}),
                "token_usage": token_usage,
            }
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse analysis response as JSON: {full_text[:200]}")
            return {
                "insight": full_text,
                "context_summary": "Analysis provided as text.",
                "chart_config": {"chart_type": "table", "title": "Results"},
                "token_usage": token_usage,
            }

    def _format_result_preview(self, columns: list[str], rows: list[list]) -> str:
        """Format results as a readable table for the prompt."""
        if not rows:
            return "(empty result set)"

        lines = [" | ".join(columns)]
        lines.append("-" * len(lines[0]))
        for row in rows[:20]:
            lines.append(" | ".join(str(v) for v in row))
        if len(rows) > 20:
            lines.append(f"... ({len(rows) - 20} more rows)")
        return "\n".join(lines)
