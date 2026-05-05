import asyncio
from datetime import datetime

import pytest
from sqlmodel import select

from app.model.UserModel import PrivateUserModel


@pytest.mark.asyncio
class TestRegistryRoute:

  async def test_registry_success(self, client, db_session):
    """测试成功注册"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    username = f"testuser_{timestamp}"
    email = f"{username}@example.com"

    response = await client.post("/registry", json={
      "username": username,
      "full_name": "测试用户",
      "email": email,
      "password": "TestPass123"
    })

    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert data["result"]["username"] == username
    assert data["result"]["email"] == email
    assert data["result"]["valid"] == "N"
    assert "valid_url" in data

    stmt = select(PrivateUserModel).where(PrivateUserModel.username == username)
    query = await db_session.execute(stmt)

    user = query.scalar_one_or_none()
    assert user is not None
    assert user.email == email

  async def test_registry_duplicate_username(self, client, db_session):
    """测试用户名已存在"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    username = f"testuser_dup_{timestamp}"
    email = f"{username}@example.com"

    await client.post("/registry", json={
      "username": username,
      "full_name": "测试用户",
      "email": email,
      "password": "TestPass123"
    })

    response = await client.post("/registry", json={
      "username": username,
      "full_name": "另一个用户",
      "email": f"another_{email}",
      "password": "TestPass123"
    })

    assert response.status_code == 400
    assert "用户名或者邮箱已经存在" in response.json()["detail"]

  async def test_registry_duplicate_email(self, client, db_session):
    """测试邮箱已存在"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    username = f"testuser_email_{timestamp}"
    email = f"{username}@example.com"

    await client.post("/registry", json={
      "username": username,
      "full_name": "测试用户",
      "email": email,
      "password": "TestPass123"
    })

    response = await client.post("/registry", json={
      "username": f"another_{username}",
      "full_name": "另一个用户",
      "email": email,
      "password": "TestPass123"
    })

    assert response.status_code == 400
    assert "用户名或者邮箱已经存在" in response.json()["detail"]

  async def test_registry_password_too_short(self, client):
    """测试密码太短"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    username = f"testuser_short_{timestamp}"
    email = f"{username}@example.com"

    response = await client.post("/registry", json={
      "username": username,
      "full_name": "测试用户",
      "email": email,
      "password": "Abc123"
    })

    assert response.status_code == 400
    assert "密码长度至少为8位" in response.json()["detail"]

  async def test_registry_password_no_uppercase(self, client):
    """测试密码没有大写字母"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    username = f"testuser_noupper_{timestamp}"
    email = f"{username}@example.com"

    response = await client.post("/registry", json={
      "username": username,
      "full_name": "测试用户",
      "email": email,
      "password": "testpass123"
    })

    assert response.status_code == 400
    assert "密码必须包含至少一个大写字母" in response.json()["detail"]

  async def test_registry_password_no_lowercase(self, client):
    """测试密码没有小写字母"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    username = f"testuser_nolower_{timestamp}"
    email = f"{username}@example.com"

    response = await client.post("/registry", json={
      "username": username,
      "full_name": "测试用户",
      "email": email,
      "password": "TESTPASS123"
    })

    assert response.status_code == 400
    assert "密码必须包含至少一个小写字母" in response.json()["detail"]

  async def test_registry_password_no_digit(self, client):
    """测试密码没有数字"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    username = f"testuser_nodigit_{timestamp}"
    email = f"{username}@example.com"

    response = await client.post("/registry", json={
      "username": username,
      "full_name": "测试用户",
      "email": email,
      "password": "TestPassTest"
    })

    assert response.status_code == 400
    assert "密码必须包含至少一个数字" in response.json()["detail"]

  async def test_registry_concurrent(self, client):
    """测试并发注册"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")

    async def register_user(i):
      username = f"concurrent_{timestamp}_{i}"
      email = f"{username}@example.com"
      return await client.post("/registry", json={
        "username": username,
        "full_name": f"并发用户{i}",
        "email": email,
        "password": "TestPass123"
      })

    tasks = [register_user(i) for i in range(3)]
    responses = await asyncio.gather(*tasks)

    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count == 3
