"""
SQL Safety Validator
====================
Uses sqlglot to PARSE the SQL into an AST, then validates the tree structure.
"""

import sqlglot
from sqlglot import exp


ALLOWED_STATEMENT_TYPES = (exp.Select,)

BLOCKED_EXPRESSION_TYPES = (
    exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter,
    exp.Command,
    exp.Transaction,
    exp.Set,
)


class SQLSafetyValidator:
    """Validates that SQL is a pure read-only SELECT statement."""

    def validate(self, sql: str) -> dict:
        if not sql or not sql.strip():
            return {"is_safe": False, "reason": "Empty SQL", "parsed_sql": None}

        try:
            statements = sqlglot.parse(sql)
        except sqlglot.errors.ParseError as e:
            return {"is_safe": False, "reason": f"SQL parse error: {e}", "parsed_sql": None}

        if len(statements) != 1:
            return {
                "is_safe": False,
                "reason": f"Expected 1 statement, got {len(statements)}. Multi-statement queries are not allowed.",
                "parsed_sql": None,
            }

        statement = statements[0]

        if not isinstance(statement, ALLOWED_STATEMENT_TYPES):
            return {
                "is_safe": False,
                "reason": f"Only SELECT statements are allowed. Got: {type(statement).__name__}",
                "parsed_sql": None,
            }

        for node in statement.walk():
            if isinstance(node, BLOCKED_EXPRESSION_TYPES):
                return {
                    "is_safe": False,
                    "reason": f"Query contains forbidden operation: {type(node).__name__}",
                    "parsed_sql": None,
                }

        normalized = statement.sql(dialect="postgres", pretty=True)
        return {"is_safe": True, "reason": None, "parsed_sql": normalized}
