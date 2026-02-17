"""Application constants."""

# User roles
ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
ROLE_VIEWER = "viewer"
ALL_ROLES = [ROLE_ADMIN, ROLE_ANALYST, ROLE_VIEWER]

# Connection types
CONN_POSTGRESQL = "postgresql"
CONN_MYSQL = "mysql"
CONN_SQLITE = "sqlite"
CONN_CSV = "csv"
CONN_EXCEL = "excel"
ALL_CONN_TYPES = [CONN_POSTGRESQL, CONN_MYSQL, CONN_SQLITE, CONN_CSV, CONN_EXCEL]

# Widget types
WIDGET_CHART = "chart"
WIDGET_TABLE = "table"
WIDGET_KPI = "kpi"
WIDGET_TEXT = "text"

# Alert condition types
ALERT_ABOVE = "above"
ALERT_BELOW = "below"
ALERT_CHANGE_PCT = "change_pct"
ALERT_ANOMALY = "anomaly"

# Query limits
MAX_QUERY_ROWS = 10000
QUERY_TIMEOUT_SECONDS = 30
RESULT_PREVIEW_ROWS = 100

# Cache
DEFAULT_CACHE_TTL_SECONDS = 300
