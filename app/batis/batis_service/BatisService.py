from __future__ import annotations

from typing import TypeVar, Generic
from typing import List as TypingList

from app.batis.batis_service.batis_batch_insert import batis_batch_insert
from app.batis.batis_service.batis_batch_update import batis_batch_update
from app.batis.batis_service.batis_delete import batis_delete
from app.batis.batis_service.batis_insert import batis_insert
from app.batis.batis_service.batis_item import batis_item
from app.batis.batis_service.batis_list import batis_list
from app.batis.batis_service.batis_update import batis_update
from app.batis.batis_utils.batis_scheme import (
  BatisModuleConfig,
  BatisItemBody,
  BatisDebugMeta,
  BatisModuleColumn,
  BatisQueryBody,
  QueryResponse,
  BatisInsertBody,
  BatisUpdateBody,
  BatisBatchInsertBody,
  BatisBatchUpdateBody,
  BatisDeleteBody,
)
from app.model.BasicModel import BasicModel
from app.utils.mysql_utils import AsyncSessionDep
from app.utils.model_utils import to_camel

# 定义类型变量，约束为 BasicModel 或其子类
T = TypeVar('T', bound=BasicModel)


class BatisService(Generic[T]):
  """
  batis服务
  """

  def __init__(
    self,
    clazz: type[T],
    # module_config.base
    base: str | None = None,
    # external module_config.columns
    external_columns: dict[str, BatisModuleColumn] | None = None,
  ):
    self.clazz = clazz
    self.module_config = _generate_module_config(clazz, base, external_columns)

  async def item(
    self,
    session: AsyncSessionDep,
    item_body: BatisItemBody,
    user: BasicModel | None = None,
    debug_data: list[BatisDebugMeta] | None = None,
  ) -> T | None:
    item_result = await batis_item(
      session=session,
      item_body=item_body,
      module_config=self.module_config,
      user=user,
      debug_data=debug_data,
    )
    if not item_result.result:
      return None
    return self.clazz.to_obj(item_result.result)

  async def list(
    self,
    session: AsyncSessionDep,
    query_body: BatisQueryBody,
    user: BasicModel | None = None,
    debug_data: list[BatisDebugMeta] | None = None,
  ) -> QueryResponse[T]:
    list_result = await batis_list(
      session=session,
      query_body=query_body,
      module_config=self.module_config,
      user=user,
      debug_data=debug_data,
    )
    return QueryResponse[T](
      list=[self.clazz.to_obj(item) for item in (list_result.list or [])],
      total=list_result.total,
      has_next=list_result.has_next,
    )

  async def insert(
    self,
    session: AsyncSessionDep,
    obj: T,
    user: BasicModel | None = None,
    debug_data: TypingList[BatisDebugMeta] | None = None,
  ) -> T | None:
    insert_result = await batis_insert(
      session=session,
      insert_body=BatisInsertBody(row=obj.to_dict()),
      module_config=self.module_config,
      user=user,
      debug_data=debug_data
    )
    if not insert_result.result:
      return None
    return self.clazz.to_obj(insert_result.result)

  async def update(
    self,
    session: AsyncSessionDep,
    obj: T,
    user: BasicModel | None = None,
    debug_data: TypingList[BatisDebugMeta] | None = None,
  ) -> T | None:
    update_result = await batis_update(
      session=session,
      update_body=BatisUpdateBody(row=obj.to_dict()),
      module_config=self.module_config,
      user=user,
      debug_data=debug_data
    )
    if not update_result.result:
      return None
    return self.clazz.to_obj(update_result.result)

  async def batch_insert(
    self,
    session: AsyncSessionDep,
    obj_list: TypingList[T],
    user: BasicModel | None = None,
    debug_data: TypingList[BatisDebugMeta] | None = None,
  ) -> TypingList[T] | None:
    batch_result = await batis_batch_insert(
      session=session,
      batch_insert_body=BatisBatchInsertBody(rows=[obj.to_dict() for obj in obj_list]),
      module_config=self.module_config,
      user=user,
      debug_data=debug_data
    )
    if not batch_result.result:
      return None
    return [self.clazz.to_obj(item) for item in batch_result.result]

  async def batch_update(
    self,
    session: AsyncSessionDep,
    obj_list: TypingList[T],
    user: BasicModel | None = None,
    debug_data: TypingList[BatisDebugMeta] | None = None,
  ) -> TypingList[T] | None:
    update_result = await batis_batch_update(
      session=session,
      batch_update_body=BatisBatchUpdateBody(rows=[obj.to_dict() for obj in obj_list]),
      module_config=self.module_config,
      user=user,
      debug_data=debug_data
    )
    if not update_result.result:
      return None
    return [self.clazz.to_obj(item) for item in update_result.result]

  async def delete(
    self,
    session: AsyncSessionDep,
    id: str | TypingList[str],
    user: BasicModel | None = None,
    debug_data: TypingList[BatisDebugMeta] | None = None,
  ) -> int | None:
    delete_result = await batis_delete(
      session=session,
      delete_body=BatisDeleteBody(id=id),
      module_config=self.module_config,
      user=user,
      debug_data=debug_data
    )
    return delete_result.affected_rows


def _generate_module_config(
  clazz: type[BasicModel],
  base: str | None = None,
  external_columns: dict[str, BatisModuleColumn] | None = None,
) -> BatisModuleConfig:
  """
  从 Model 类自动生成 BatisModuleConfig

  Args:
    clazz: SQLModel 类
    base: 模块访问路径
    external_columns: 外部列配置（优先级高于自动生成的配置）

  Returns:
    BatisModuleConfig 配置对象
  """
  # 获取表名
  table_name = getattr(clazz, '__tablename__', None)
  if not table_name:
    raise ValueError(f"Class {clazz.__name__} does not have __tablename__ attribute")

  # 获取基础路径（从表名转换）
  if not base:
    base = f"/{table_name}"

  # 获取字段信息
  columns = {}

  # 使用 model_fields 获取所有字段（Pydantic V2）
  if hasattr(clazz, 'model_fields'):
    fields = clazz.model_fields
  else:
    raise ValueError(f"Class {clazz.__name__} does not have model_fields")

  for field_name, field_info in fields.items():
    # 转换为驼峰命名
    hump_name = to_camel(field_name)

    # 推断值类型
    field_type = field_info.annotation
    if field_type is None:
      value_type = 'string'
    else:
      value_type = _infer_value_type(field_type)

    # 创建列配置
    columns[hump_name] = BatisModuleColumn(value_type=value_type)

  # 生成模块配置
  # 注意：external_columns 放在后面，优先级更高，可以覆盖自动生成的配置
  module_config = BatisModuleConfig.to_obj({
    "tableName": table_name,
    "base": base,
    "columns": {
      **{k: v.to_dict() for k, v in columns.items()},
      **(external_columns if external_columns else {})
    }
  })

  return module_config


def _infer_value_type(python_type: type) -> str:
  """根据 Python 类型推断 Batis 的 valueType"""
  # 处理 Optional 类型（Union[X, None]）
  if hasattr(python_type, '__origin__'):
    args = getattr(python_type, '__args__', ())
    if args:
      python_type = args[0]

  type_name = python_type.__name__ if hasattr(python_type, '__name__') else str(python_type)

  type_mapping = {
    'str': 'string',
    'int': 'number',
    'float': 'number',
    'bool': 'boolean',
    'datetime': 'datetime',
    'date': 'date',
    'time': 'time',
    'Decimal': 'number',
    # 项目自定义类型
    'FormattedDatetime': 'datetime',
    'FormattedDate': 'date',
    'FormattedTime': 'time',
    'FormattedDecimal': 'number',
  }

  return type_mapping.get(type_name, 'string')
