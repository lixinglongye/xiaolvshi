import json

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from core.database import get_db
from dependencies.auth import get_current_user
from models.cases import Cases
from routers.cases import router
from schemas.auth import UserResponse


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Cases.__table__.create)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture
async def app(db_session):
    app = FastAPI()
    app.include_router(router)

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app


def _user(user_id: str, email: str = "user@example.test", name: str = "User", role: str = "user") -> UserResponse:
    return UserResponse(id=user_id, email=email, name=name, role=role)


async def _seed_case(db_session):
    case = Cases(
        user_id="owner-user",
        title="Runtime router case",
        client_name="Private Client",
        team_members=json.dumps(
            [
                {"user_id": "lawyer-user", "role": "lawyer"},
                {"user_id": "reviewer-user", "role": "reviewer"},
                {"user_id": "assistant-user", "role": "assistant"},
            ]
        ),
    )
    db_session.add(case)
    await db_session.commit()
    await db_session.refresh(case)
    return case


def _client(app: FastAPI, user: UserResponse) -> TestClient:
    async def override_user():
        return user

    app.dependency_overrides[get_current_user] = override_user
    return TestClient(app)


@pytest.mark.asyncio
async def test_case_runtime_permissions_allow_lawyer_to_read_and_update(app, db_session):
    case = await _seed_case(db_session)
    client = _client(app, _user("lawyer-user"))

    read_response = client.get(f"/api/v1/entities/cases/{case.id}")
    assert read_response.status_code == 200
    assert read_response.json()["title"] == "Runtime router case"

    permission_response = client.get(f"/api/v1/entities/cases/{case.id}/permissions")
    assert permission_response.status_code == 200
    permissions = permission_response.json()
    assert permissions["actor_role"] == "lawyer"
    assert "write" in permissions["allowed_operations"]
    assert "Private Client" not in json.dumps(permissions)

    update_response = client.put(f"/api/v1/entities/cases/{case.id}", json={"stage": "trial"})
    assert update_response.status_code == 200
    assert update_response.json()["stage"] == "trial"


@pytest.mark.asyncio
async def test_case_runtime_permissions_block_reviewer_and_assistant_writes(app, db_session):
    case = await _seed_case(db_session)

    reviewer_response = _client(app, _user("reviewer-user")).put(
        f"/api/v1/entities/cases/{case.id}",
        json={"stage": "closed"},
    )
    assert reviewer_response.status_code == 403
    assert reviewer_response.json()["detail"]["status"] == "denied"
    assert reviewer_response.json()["detail"]["actor_role"] == "reviewer"

    assistant_response = _client(app, _user("assistant-user")).put(
        f"/api/v1/entities/cases/{case.id}",
        json={"stage": "draft"},
    )
    assert assistant_response.status_code == 403
    detail = assistant_response.json()["detail"]
    assert detail["status"] == "requires_approval"
    assert detail["approval_gate"] == "lawyer_or_owner_write_approval"
    assert "Private Client" not in json.dumps(detail)


@pytest.mark.asyncio
async def test_case_runtime_permissions_filter_list_and_all_routes(app, db_session):
    case = await _seed_case(db_session)

    outsider_client = _client(app, _user("outsider-user"))
    assert outsider_client.get(f"/api/v1/entities/cases/{case.id}").status_code == 403
    assert outsider_client.get("/api/v1/entities/cases?limit=2000").json()["total"] == 0
    assert outsider_client.get("/api/v1/entities/cases/all?limit=2000").json()["total"] == 0

    owner_client = _client(app, _user("owner-user"))
    owner_list = owner_client.get("/api/v1/entities/cases/all?limit=2000")
    assert owner_list.status_code == 200
    assert owner_list.json()["total"] == 1
    assert owner_list.json()["items"][0]["id"] == case.id
