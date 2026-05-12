# tests/conftest.py
import asyncio
import datetime

import pytest
from httpx import AsyncClient, ASGITransport

from app.auth.token_utils import token_utils
from app.config.env import env
from app.main import app
from app.utils.mysql_utils import async_session
from app.utils.redis_utils import RedisUtils


@pytest.fixture(scope="function")
async def client():
  access_token = token_utils.create_token(
    username="lisi",
    token_type="access",
    expires_delta=datetime.timedelta(days=1),
  )
  async with AsyncClient(
    transport=ASGITransport(app=app),
    base_url="http://test",
    headers={
      "Authorization": f"Bearer {access_token}",
    }
  ) as ac:
    yield ac


@pytest.fixture(scope="function")
async def db_session():
  async with async_session() as session:
    yield session
    await session.rollback()
