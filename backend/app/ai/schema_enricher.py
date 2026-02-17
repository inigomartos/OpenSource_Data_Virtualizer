"""AI-generated schema descriptions and business term mappings."""

import json
from anthropic import AsyncAnthropic
from app.ai.prompts import SYSTEM_PROMPT_SCHEMA_ENRICHMENT
from loguru import logger


class SchemaEnricher:
    def __init__(self, client: AsyncAnthropic, model: str = "claude-sonnet-4-20250514"):
        self.client = client
        self.model = model

    async def enrich_schema(self, schema_info: str) -> dict:
        """Use Claude to generate descriptions for tables and columns."""
        prompt = SYSTEM_PROMPT_SCHEMA_ENRICHMENT.format(schema_info=schema_info)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            system="You are a database schema analyst.",
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = response.content[0].text

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse schema enrichment response")
            return {"tables": []}
