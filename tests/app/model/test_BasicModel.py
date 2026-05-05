# --- 测试用子类 ---
from datetime import datetime

import pytest
from sqlmodel import Field

from app.model.BasicModel import BasicModel


# --- 业务模拟模型 ---
class MockTask(BasicModel):
  task_name: str
  priority_level: int = 1
  is_finished: bool = False


# --- 异步测试脚本 ---
@pytest.mark.asyncio
class TestMockTask:

  async def test_to_dict_full_structure(self):
    """验证 to_dict 生成的 JSON 结构是否完全符合小驼峰要求"""

    # 1. 初始化模型
    # 注意：这里我们手动传入时间，确保断言时字符串匹配
    fixed_time = datetime(2026, 4, 23, 13, 0, 0)
    time_str = "2026-04-23 13:00:00"

    task = MockTask(
      id="task-001",
      task_name="学习 Gemini API",
      priority_level=5,
      is_finished=True,
      created_at=fixed_time,
      updated_at=fixed_time,
      created_by="user_admin"
    )

    # 2. 执行转换
    result = task.to_dict()

    # 3. 定义预期的 JSON 结构 (完全匹配验证)
    # Pytest 会在失败时逐行对比这里的差异
    expected = {
      "id": "task-001",
      "taskName": "学习 Gemini API",
      "priorityLevel": 5,
      "isFinished": True,
      "createdAt": time_str,  # 验证 json_encoders 是否生效
      "updatedAt": time_str,
      "createdBy": "user_admin",
      "updatedBy": None  # 验证默认值
    }

    # 4. 断言
    assert result == expected

  async def test_to_obj_from_camel_json(self):
    """验证从小驼峰字典（模拟前端输入）恢复为 Python 对象"""
    input_json = {
      "taskName": "重构代码",
      "priorityLevel": 2,
      "isFinished": False,
      "id": "task-002"
    }

    task = MockTask.to_obj(input_json)

    # 验证属性是否正确映射回 snake_case
    assert task.task_name == "重构代码"
    assert task.priority_level == 2
    assert task.is_finished is False
    assert task.id == "task-002"

  async def test_default_factory_execution(self):
    """验证默认工厂函数（时间戳）是否正常工作"""
    task = MockTask(task_name="自动生成时间测试")
    result = task.to_dict()

    # 验证自动生成的字段是否存在且格式正确
    assert "createdAt" in result
    assert isinstance(result["createdAt"], str)
    assert len(result["createdAt"]) == 19  # YYYY-MM-DD HH:MM:SS
