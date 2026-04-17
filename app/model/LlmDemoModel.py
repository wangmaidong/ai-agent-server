import uuid
from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from typing import List

from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import SQLModel, Field, select

from app.utils.mysql_utils import AsyncSessionDep

# 定义北京时区（UTC+8）
beijing_timezone = timezone(timedelta(hours=8))

# 定义获取当前北京时区时间的匿名函数，用于默认值生成
current_datetime = lambda: datetime.now(beijing_timezone)


class LlmDemoModel(SQLModel, table=True):
  __tablename__ = "llm_demo"

  id: str = Field(default=None, primary_key=True, description="唯一标识，编号")
  created_at: datetime = Field(default_factory=current_datetime, description="创建时间")
  updated_at: datetime = Field(default_factory=current_datetime, description="更新时间")
  created_by: str | None = Field(default=None, description="创建人id")
  updated_by: str | None = Field(default=None, description="更新人id")

  full_name: str = Field(default=None, description="用户名称")
  datetime_start: datetime = Field(default=None, description="开通会员时间")
  datetime_end: datetime = Field(default=None, description="会员截止到期时间")
  birthday: date = Field(default=None, description="生日")
  amount: Decimal = Field(default=0, description="金额")


def add_llm_demo_route(app: FastAPI):
  route_prefix = "/llm_demo"
  router = APIRouter(prefix=route_prefix, tags=[route_prefix])

  @router.post('/list')
  async def _list(
    session: AsyncSessionDep,
    body: ModelQuerySchema = ModelQuerySchema(),
  ):
    """
    获取所有用户列表
    """

    # 构建SQL查询执行对象
    query = select(LlmDemoModel).order_by(
      LlmDemoModel.created_at.desc()
    )
    # 计算偏移量（跳过前N条），并查询比一页多1条的记录（用于判断是否有下一页）
    query = query.offset(body.page * body.page_size).limit(body.page_size + 1)
    result = await session.execute(query)
    query_cls_list: List[LlmDemoModel] = result.scalars().all()
    has_next = len(query_cls_list) == body.page_size + 1
    # 若有下一页，移除多查询的那一条记录
    if has_next:
      query_cls_list.pop()
    return {
      "list": query_cls_list,
      "has_next": has_next
    }

  @router.post('/insert')
  async def _insert(body: LlmDemoModel, session: AsyncSessionDep):
    """
    插入用户
    """
    if not body.id:
      body.id = str(uuid.uuid4())
    session.add(body)
    await session.commit()
    return body

  @router.post('/update')
  async def _update(body: LlmDemoModel, session: AsyncSessionDep):
    """
    更新用户
    """
    query = select(LlmDemoModel).where(LlmDemoModel.id == body.id)
    result = await session.execute(query)
    query_cls = result.scalars().first()
    if not query_cls:
      raise HTTPException(status_code=500, detail=f"Update row with id:{body.id} not found")

    update_data_exclude_true = body.model_dump(exclude_unset=True, exclude={'id'})
    update_data_exclude_false = body.model_dump(exclude={'id'})

    print(f"update_data_exclude_true: {update_data_exclude_true}")
    print(f"update_data_exclude_false: {update_data_exclude_false}")

    update_data = body.model_dump(exclude_unset=True, exclude={'id'})
    for field, value in update_data.items():
      setattr(query_cls, field, value)
    session.add(query_cls)
    await session.commit()
    return query_cls

  @router.post('/delete')
  async def _delete(body: LlmDemoModel, session: AsyncSessionDep):
    """
    更新用户
    """
    query = select(LlmDemoModel).where(LlmDemoModel.id == body.id)
    result = await session.execute(query)
    query_cls = result.scalars().first()
    if not query_cls:
      return {"affect_row_count": 0}
    await session.delete(query_cls)
    await session.commit()
    return {"affect_row_count": 1}

  app.include_router(router)


class ModelQuerySchema(BaseModel):
  page: int = Field(default=0, description="页码")
  page_size: int = Field(default=5, description="每页数量")
