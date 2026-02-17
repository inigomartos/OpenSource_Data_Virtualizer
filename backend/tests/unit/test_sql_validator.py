"""SQL validator unit tests including adversarial cases."""

import pytest
from app.core.sql_validator import SQLSafetyValidator

validator = SQLSafetyValidator()


class TestSQLValidatorBasic:
    def test_valid_select(self):
        result = validator.validate("SELECT * FROM users")
        assert result["is_safe"] is True

    def test_valid_select_with_where(self):
        result = validator.validate("SELECT name, email FROM users WHERE active = true")
        assert result["is_safe"] is True

    def test_valid_select_with_join(self):
        result = validator.validate(
            "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id"
        )
        assert result["is_safe"] is True

    def test_valid_cte(self):
        result = validator.validate(
            "WITH top_users AS (SELECT * FROM users LIMIT 10) SELECT * FROM top_users"
        )
        assert result["is_safe"] is True

    def test_valid_aggregate(self):
        result = validator.validate(
            "SELECT region, SUM(revenue) as total FROM sales GROUP BY region ORDER BY total DESC"
        )
        assert result["is_safe"] is True

    def test_empty_sql(self):
        result = validator.validate("")
        assert result["is_safe"] is False

    def test_none_sql(self):
        result = validator.validate(None)
        assert result["is_safe"] is False


class TestSQLValidatorAdversarial:
    """Every one of these MUST be blocked."""

    def test_multi_statement_drop(self):
        result = validator.validate("SELECT 1; DROP TABLE users;")
        assert result["is_safe"] is False

    def test_insert(self):
        result = validator.validate("INSERT INTO users (name) VALUES ('hacker')")
        assert result["is_safe"] is False

    def test_update(self):
        result = validator.validate("UPDATE users SET role = 'admin' WHERE id = 1")
        assert result["is_safe"] is False

    def test_delete(self):
        result = validator.validate("DELETE FROM users WHERE id = 1")
        assert result["is_safe"] is False

    def test_drop_table(self):
        result = validator.validate("DROP TABLE users")
        assert result["is_safe"] is False

    def test_whitespace_padded_dml(self):
        result = validator.validate("   \n\t  DROP TABLE users  ")
        assert result["is_safe"] is False

    def test_trailing_grant(self):
        result = validator.validate("SELECT CAST(1 AS INT); GRANT ALL ON users TO public")
        assert result["is_safe"] is False

    def test_keyword_in_string_literal_should_pass(self):
        """Keywords in string literals are safe -- they're just data."""
        result = validator.validate("SELECT * FROM users WHERE name = 'DROP TABLE'")
        assert result["is_safe"] is True
