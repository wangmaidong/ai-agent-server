# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.config.env import env
from app.utils.mysql_utils import async_session


@pytest.fixture(scope="function")
async def client():
  async with AsyncClient(base_url=f"http://localhost:{env.server_port}") as ac:
    yield ac


@pytest.fixture(scope="function")
async def db_session():
  async with async_session() as session:
    yield session
    await session.rollback()
