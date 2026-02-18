"""
DataMind AI Engine
==================
Orchestrates: User Question -> Schema Context -> Claude (NL->SQL) -> Execute -> Claude (Analyze+Visualize) -> Response

DESIGN DECISIONS (v2):
  - Dependencies are INJECTED, not instantiated internally (testability)
  - Insight + chart recommendation MERGED into one API call (latency)
  - Conversation context is CONDENSED (token efficiency)
  - SQL validation uses sqlglot PARSER, not regex (security)
  - Query results are CACHED in Redis (performance)
"""

import hashlib
from typing import Optional, Protocol

from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.sql_generator import SQLGenerator
from app.ai.analyze_and_visualize import AnalyzeAndVisualize
from app.ai.conversation import ConversationManager
from app.core.sql_validator import SQLSafetyValidator
from app.schemas.chat import ChatResponse
from app.services.token_budget_service import TokenBudgetService, TokenBudgetExceeded
from loguru import logger


class SchemaProvider(Protocol):
    async def get_schema_context(self, connection_id: str, db: AsyncSession) -> str: ...


class QueryRunner(Protocol):
    async def execute(self, connection_id: str, sql: str, db: AsyncSession,
                      timeout_seconds: int, max_rows: int, skip_validation: bool = False) -> dict: ...


class CacheProvider(Protocol):
    async def get(self, key: str) -> Optional[dict]: ...
    async def set(self, key: str, value: dict, ttl_seconds: int) -> None: ...


class AIEngine:
    """The brain of DataMind. Converts natural language into data insights."""

    def __init__(
        self,
        schema_provider: SchemaProvider,
        query_runner: QueryRunner,
        sql_validator: SQLSafetyValidator,
        cache_provider: CacheProvider,
        conversation_provider: ConversationManager,
        anthropic_client: Optional[AsyncAnthropic] = None,
        model: str = "claude-sonnet-4-20250514",
    ):
        self.client = anthropic_client or AsyncAnthropic()
        self.model = model
        self.schema_provider = schema_provider
        self.query_runner = query_runner
        self.sql_validator = sql_validator
        self.cache = cache_provider
        self.conversation = conversation_provider
        self.sql_generator = SQLGenerator(self.client, model)
        self.analyzer = AnalyzeAndVisualize(self.client, model)

    async def process_message(
        self,
        user_message: str,
        connection_id: str,
        session_id: str,
        db: AsyncSession,
        on_stream: Optional[callable] = None,
        org_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        Full pipeline:
            0. Check token budget (if org_id provided)
            1. Load schema context
            2. Load condensed conversation history
            3. Generate SQL via Claude
            4. Validate SQL via sqlglot parser
            5. Check cache -> execute if miss
            6. Analyze results + recommend chart (single Claude call)
            7. Record token usage & return response
        """

        # Step 0: Token Budget Check
        budget_service = TokenBudgetService()
        if org_id:
            try:
                await budget_service.check_budget(org_id, db)
            except TokenBudgetExceeded as exc:
                return ChatResponse(
                    content=(
                        "Your organization has reached its monthly AI token budget. "
                        "Please contact your administrator to upgrade the plan or "
                        "wait for the budget to reset."
                    ),
                    error_message=str(exc),
                )

        # Step 1: Schema Context
        schema_context = await self.schema_provider.get_schema_context(
            connection_id=connection_id, db=db,
        )

        # Step 2: Condensed Conversation History
        history = await self.conversation.get_condensed_history(
            session_id=session_id, db=db, max_turns=10,
        )

        # Step 3: Generate SQL
        sql_response = await self.sql_generator.generate(
            user_message=user_message,
            schema_context=schema_context,
            conversation_history=history,
            on_stream=on_stream,
        )
        generated_sql = sql_response["sql"]

        # Handle non-data queries
        if generated_sql in ("CANNOT_ANSWER", "NOT_DATA_QUERY"):
            return ChatResponse(
                content=sql_response.get("reasoning", "I can only answer questions about your data."),
                generated_sql=None,
                token_usage=sql_response.get("token_usage"),
            )

        # Step 4: Validate SQL (sqlglot parser -- NOT regex)
        validation = self.sql_validator.validate(generated_sql)
        if not validation["is_safe"]:
            return ChatResponse(
                content=f"I generated a query but it was blocked for safety: {validation['reason']}. "
                        f"I can only run read-only queries. Could you rephrase?",
                generated_sql=generated_sql,
                error_message=validation["reason"],
            )

        # Step 5: Check Cache -> Execute
        cache_key = hashlib.sha256(f"{connection_id}:{generated_sql}".encode()).hexdigest()
        cached = await self.cache.get(cache_key)

        if cached:
            execution_result = cached
            logger.info(f"Cache hit for query: {cache_key[:16]}...")
        else:
            execution_result = await self.query_runner.execute(
                connection_id=connection_id,
                sql=generated_sql,
                db=db,
                timeout_seconds=30,
                max_rows=10000,
                skip_validation=True,
            )

            # Retry logic: if SQL execution failed, retry once with error context
            if execution_result.get("error"):
                retry_prompt = (
                    f"The SQL query failed with error: {execution_result['error']}. "
                    f"Original question: {user_message}\n"
                    f"Please fix the SQL and try again."
                )
                retry_response = await self.sql_generator.generate(
                    user_message=retry_prompt,
                    schema_context=schema_context,
                    conversation_history=history,
                    on_stream=on_stream,
                )
                retry_sql = retry_response.get("sql")
                if retry_sql and retry_sql not in ("CANNOT_ANSWER", "NOT_DATA_QUERY"):
                    # Validate the retry SQL
                    retry_validation = self.sql_validator.validate(retry_sql)
                    if retry_validation["is_safe"]:
                        # Merge token usage from retry attempt
                        sql_response_tokens = sql_response.get("token_usage", {})
                        retry_tokens = retry_response.get("token_usage", {})
                        sql_response["token_usage"] = {
                            "input_tokens": sql_response_tokens.get("input_tokens", 0) + retry_tokens.get("input_tokens", 0),
                            "output_tokens": sql_response_tokens.get("output_tokens", 0) + retry_tokens.get("output_tokens", 0),
                        }
                        generated_sql = retry_sql
                        execution_result = await self.query_runner.execute(
                            connection_id=connection_id,
                            sql=retry_sql,
                            db=db,
                            timeout_seconds=30,
                            max_rows=10000,
                            skip_validation=True,
                        )

            # If still an error after retry, return it to the user
            if execution_result.get("error"):
                return ChatResponse(
                    content=f"I ran into an issue querying your data: {execution_result['error']}. "
                            f"Could you try rephrasing?",
                    generated_sql=generated_sql,
                    error_message=execution_result["error"],
                )

            await self.cache.set(cache_key, execution_result, ttl_seconds=300)

        # Step 6: Analyze + Visualize (SINGLE Claude call)
        analysis = await self.analyzer.analyze(
            user_message=user_message,
            sql=generated_sql,
            result_data=execution_result["data"],
            on_stream=on_stream,
        )

        # Merge token usage from both steps
        sql_tokens = sql_response.get("token_usage", {})
        analysis_tokens = analysis.get("token_usage", {})
        total_tokens = {
            "input_tokens": sql_tokens.get("input_tokens", 0) + analysis_tokens.get("input_tokens", 0),
            "output_tokens": sql_tokens.get("output_tokens", 0) + analysis_tokens.get("output_tokens", 0),
        }

        # Step 7: Record token usage against org budget
        if org_id:
            await budget_service.record_usage(
                org_id=org_id,
                input_tokens=total_tokens.get("input_tokens", 0),
                output_tokens=total_tokens.get("output_tokens", 0),
                db=db,
            )

        return ChatResponse(
            content=analysis["insight"],
            context_summary=analysis["context_summary"],
            generated_sql=generated_sql,
            query_result_preview=self._truncate_result(execution_result["data"], max_rows=100),
            full_result_row_count=execution_result["data"].get("row_count", 0),
            chart_config=analysis["chart_config"],
            execution_time_ms=execution_result.get("execution_time_ms"),
            token_usage=total_tokens,
        )

    def _truncate_result(self, data: dict, max_rows: int = 100) -> dict:
        """Store only a preview of results in the DB."""
        rows = data.get("rows", [])
        return {
            "columns": data.get("columns", []),
            "rows": rows[:max_rows],
            "row_count": min(len(rows), max_rows),
            "truncated": len(rows) > max_rows,
        }
