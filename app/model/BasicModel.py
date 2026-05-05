import json
from datetime import datetime, date
from typing import Any, Self

from pydantic import ConfigDict
from sqlmodel import SQLModel, Field

from app.utils.model_utils import to_camel, format_datetime_to_string, format_date_to_string, FormattedDatetime, current_datetime


class BasicModel(SQLModel):
  # Pydantic V2 的模型配置
  model_config = ConfigDict(
    alias_generator=to_camel,  # 使用 to_camel 函数生成别名
    populate_by_name=True,  # 允许通过原始字段名（snake_case）赋值
    extra='ignore',  # 忽略模型中未定义的额外字段，避免验证失败
    json_encoders={
      datetime: format_datetime_to_string,  # 为 datetime 类型指定自定义的 JSON 编码器
      date: format_date_to_string  # 为 date 类型指定自定义的 JSON 编码器
    }
  )

  id: str | None = Field(default=None, primary_key=True, description="唯一标识，编号")
  created_at: FormattedDatetime | None = Field(default_factory=current_datetime, description="创建时间")
  updated_at: FormattedDatetime | None = Field(default_factory=current_datetime, description="更新时间")
  created_by: str | None = Field(default=None, description="创建人id")
  updated_by: str | None = Field(default=None, description="更新人id")

  def to_dict(self, **kwargs) -> dict[str, Any]:
    """
    将当前实例转换为字典。
    默认开启 by_alias=True (转为小驼峰)
    """
    return json.loads(self.model_dump_json(by_alias=True, **kwargs))

  @classmethod
  def to_obj(cls, data: dict[str, Any]) -> Self:
    """
    将字典转换为当前类的实例对象。
    """
    return cls.model_validate(data)


if __name__ == "__main__":
  item_obj = BasicModel(id="1", created_at=datetime.now(), updated_at=datetime.now())
  print(item_obj)
  item_dict = item_obj.to_dict()
  if not isinstance(item_dict, dict):
    raise Exception(f"to_dict() 返回值类型错误，当前值类型为 {type(item_dict)}")
  print(f"item_dict: {item_dict}")
  new_obj = BasicModel.to_obj(item_dict)
  if not isinstance(new_obj, BasicModel):
    raise Exception(f"to_obj() 错误，当前值类型为 {type(new_obj)}")
  print(f"new_obj: {new_obj}")
