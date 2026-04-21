import uuid
from typing import List

from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import select

from app.model.BasicModel import BasicModel
from app.utils.mysql_utils import AsyncSessionDep
from app.utils.path_join import path_join


def add_model_routes(app: FastAPI, clazz: type[BasicModel], route_prefix: str):
  route_prefix = '/general' + route_prefix
  router = APIRouter(prefix=route_prefix, tags=[route_prefix])

  # 分页查询参数
  class ListQuerySchema(BasicModel):
    page: int | None = Field(default=0, description="页码")
    page_size: int | None = Field(default=5, description="每页数量")

  # 单条记录查询参数
  class ItemQuerySchema(BaseModel):
    id: str = Field(description="数据的ID")

  # 新建接口参数类型
  class InsertBodySchema(BaseModel):
    row: clazz = Field(description="要新建的数据")

  # 更新接口参数类型
  class UpdateBodySchema(BaseModel):
    row: clazz = Field(description="要更新的数据")

  @router.post('/list')
  async def _list(
    session: AsyncSessionDep,
    body: ListQuerySchema = ListQuerySchema(),
  ):
    """
    获取所有用户列表
    """

    # 构建SQL查询执行对象
    query = select(clazz).order_by(clazz.created_at.desc())
    # 计算偏移量（跳过前N条），并查询比一页多1条的记录（用于判断是否有下一页）
    query = query.offset(body.page * body.page_size).limit(body.page_size + 1)
    result = await session.execute(query)
    query_cls_list: List[clazz] = result.scalars().all()
    has_next = len(query_cls_list) == body.page_size + 1
    # 若有下一页，移除多查询的那一条记录
    if has_next:
      query_cls_list.pop()
    return {
      "list": query_cls_list,
      "has_next": has_next
    }

  @router.post('/item')
  async def _item(body: ItemQuerySchema, session: AsyncSessionDep):
    """
    获取记录详情
    """
    query = select(clazz).where(clazz.id == body.id)
    result = await session.execute(query)
    query_cls = result.scalars().first()
    return {"result": query_cls}

  @router.post('/insert')
  async def _insert(body: InsertBodySchema, session: AsyncSessionDep):
    """
    插入记录
    """
    new_obj = body.row
    if not new_obj.id:
      new_obj.id = str(uuid.uuid4())
    session.add(new_obj)
    await session.commit()
    return new_obj

  @router.post('/update')
  async def _update(body: UpdateBodySchema, session: AsyncSessionDep):
    """
    更新记录
    """
    edit_obj = body.row
    query = select(clazz).where(clazz.id == edit_obj.id)
    result = await session.execute(query)
    query_cls = result.scalars().first()
    if not query_cls:
      raise HTTPException(status_code=500, detail=f"Update row with id:{edit_obj.id} not found")

    update_data_exclude_true = edit_obj.model_dump(exclude_unset=True, exclude={'id'})
    update_data_exclude_false = edit_obj.model_dump(exclude={'id'})

    print(f"update_data_exclude_true: {update_data_exclude_true}")
    print(f"update_data_exclude_false: {update_data_exclude_false}")

    update_data = edit_obj.model_dump(exclude_unset=True, exclude={'id'})
    for field, value in update_data.items():
      setattr(query_cls, field, value)
    session.add(query_cls)
    await session.commit()
    return query_cls

  @router.post('/delete')
  async def _delete(body: clazz, session: AsyncSessionDep):
    """
    删除记录
    """
    query = select(clazz).where(clazz.id == body.id)
    result = await session.execute(query)
    query_cls = result.scalars().first()
    if not query_cls:
      return {"affect_row_count": 0}
    await session.delete(query_cls)
    await session.commit()
    return {"affect_row_count": 1}

  app.include_router(router)
