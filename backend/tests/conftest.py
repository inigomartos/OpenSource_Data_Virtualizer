"""Test fixtures: DB sessions, auth helpers, factory setup."""

import asyncio
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.models.base import Base
from app.main import app
from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.models.organization import Organization
from app.models.user import User
from app.models.connection import Connection

# Use SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Generate valid auth headers for testing."""
    def _headers(user_id: str = "test-user-id", role: str = "admin", org_id: str = "test-org-id"):
        token = create_access_token({
            "sub": user_id,
            "org_id": org_id,
            "email": "test@test.com",
            "role": role,
        })
        return {"Authorization": f"Bearer {token}"}
    return _headers


@pytest.fixture
async def test_org(db_session: AsyncSession) -> Organization:
    """Create a test organization."""
    org = Organization(
        id=uuid.uuid4(),
        name="Test Organization",
        slug="test-org",
    )
    db_session.add(org)
    await db_session.flush()
    await db_session.refresh(org)
    return org


@pytest.fixture
async def test_user(db_session: AsyncSession, test_org: Organization) -> User:
    """Create a test user in the test org."""
    user = User(
        id=uuid.uuid4(),
        org_id=test_org.id,
        email="testuser@test.com",
        password_hash=hash_password("testpassword123"),
        full_name="Test User",
        role="admin",
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def user_auth_headers(test_user: User):
    """Auth headers tied to the test_user fixture."""
    token = create_access_token({
        "sub": str(test_user.id),
        "org_id": str(test_user.org_id),
        "email": test_user.email,
        "role": test_user.role,
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def test_connection(db_session: AsyncSession, test_org: Organization, test_user: User) -> Connection:
    """Create a test database connection."""
    conn = Connection(
        id=uuid.uuid4(),
        org_id=test_org.id,
        created_by_id=test_user.id,
        name="Test PostgreSQL",
        type="postgresql",
        host="localhost",
        port=5432,
        database_name="test_db",
        username="test_user",
        is_active=True,
    )
    db_session.add(conn)
    await db_session.flush()
    await db_session.refresh(conn)
    return conn
