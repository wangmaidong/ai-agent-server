from datetime import datetime

import pytest

from app.model.BasicModel import BasicModel


@pytest.mark.asyncio
async def test_basic_model():
  item_obj = BasicModel(id="1", created_at=datetime.now(), updated_at=datetime.now())
  print(item_obj)
  item_dict = item_obj.to_dict()
  assert item_dict == {
    "id": "1",
    "createdAt": item_obj.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    "updatedAt": item_obj.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
    "createdBy": None,
    "updatedBy": None,
  }
  if not isinstance(item_dict, dict):
    raise Exception(f"to_dict() 返回值类型错误，当前值类型为 {type(item_dict)}")
  print(f"item_dict: {item_dict}")
  new_obj = BasicModel.to_obj(item_dict)
  if not isinstance(new_obj, BasicModel):
    raise Exception(f"to_obj() 错误，当前值类型为 {type(new_obj)}")
  print(f"new_obj: {new_obj}")
