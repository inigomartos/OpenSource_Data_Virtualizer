"""Custom exception hierarchy."""

from fastapi import HTTPException, status


class DataMindException(Exception):
    """Base exception for DataMind."""
    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(DataMindException):
    """Authentication failed."""
    pass


class AuthorizationError(DataMindException):
    """Insufficient permissions."""
    pass


class DataMindConnectionError(DataMindException):
    """Database connection failed."""
    pass


ConnectionError = DataMindConnectionError  # backward compat alias


class SQLValidationError(DataMindException):
    """SQL failed safety validation."""
    pass


class QueryExecutionError(DataMindException):
    """SQL query execution failed."""
    pass


class NotFoundError(DataMindException):
    """Resource not found."""
    pass


def raise_not_found(resource: str = "Resource"):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found")


def raise_forbidden(detail: str = "Insufficient permissions"):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def raise_unauthorized(detail: str = "Could not validate credentials"):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )
