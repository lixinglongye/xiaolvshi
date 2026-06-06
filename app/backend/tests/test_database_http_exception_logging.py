import logging

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from core.database import db_manager, get_db


@pytest.mark.asyncio
async def test_get_db_does_not_log_http_exception_as_database_error(caplog):
    old_engine = db_manager.engine
    old_session_maker = db_manager.async_session_maker
    old_initialized = db_manager._initialized

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    db_manager.engine = engine
    db_manager.async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    db_manager._initialized = True

    app = FastAPI()

    @app.get("/missing")
    async def missing(_db=Depends(get_db)):
        raise HTTPException(status_code=404, detail="missing")

    try:
        caplog.set_level(logging.ERROR, logger="core.database")

        response = TestClient(app).get("/missing")

        assert response.status_code == 404
        messages = "\n".join(record.getMessage() for record in caplog.records if record.name == "core.database")
        assert "Database session error" not in messages
        assert "Failed to create database session" not in messages
    finally:
        db_manager.engine = old_engine
        db_manager.async_session_maker = old_session_maker
        db_manager._initialized = old_initialized
        await engine.dispose()
