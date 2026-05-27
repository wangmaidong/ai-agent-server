from enum import Enum

from fastapi import FastAPI, APIRouter
from starlette.requests import Request

from app.batis.batis_service.BatisService import BatisService
from app.batis.batis_service.batis_batch_insert import batis_batch_insert
from app.batis.batis_service.batis_batch_update import batis_batch_update
from app.batis.batis_service.batis_delete import batis_delete
from app.batis.batis_service.batis_insert import batis_insert
from app.batis.batis_service.batis_item import batis_item
from app.batis.batis_service.batis_list import batis_list
from app.batis.batis_service.batis_update import batis_update
from app.batis.batis_utils.batis_scheme import BatisModuleColumn, BatisQueryBody, BatisItemBody, BatisInsertBody, BatisUpdateBody, BatisBatchInsertBody, BatisBatchUpdateBody, BatisDeleteBody
from app.model.BasicModel import BasicModel
from app.utils.mysql_utils import AsyncSessionDep
from app.utils.path_join import path_join

def add_batis_route(
  app: FastAPI,
  clazz: type[BasicModel],
  # module_config.base
  base: str | None = None,
  # external module_config.columns
  external_columns: dict[str, BatisModuleColumn] | None = None,
):
  batis_service = BatisService(clazz=clazz, base=base, external_columns=external_columns)

  route_prefix = path_join('/general/', base)
  router = APIRouter(prefix=route_prefix, tags=[route_prefix])

  @router.post("/list")
  async def _list(
    request: Request,
    session: AsyncSessionDep,
    query_body: BatisQueryBody = BatisQueryBody(),
  ):
    return await batis_list(
      session=session,
      module_config=batis_service.module_config,
      user=request.state.user,
      query_body=query_body,
    )

  @router.post('/item')
  async def _item(
    request: Request,
    session: AsyncSessionDep,
    item_body: BatisItemBody,
  ):
    return await batis_item(
      session=session,
      module_config=batis_service.module_config,
      user=request.state.user,
      item_body=item_body,
    )

  @router.post('/insert')
  async def _insert(
    request: Request,
    session: AsyncSessionDep,
    insert_body: BatisInsertBody,
  ):
    return await batis_insert(
      session=session,
      module_config=batis_service.module_config,
      user=request.state.user,
      insert_body=insert_body,
      auto_commit=True,
    )

  @router.post('/batchInsert')
  async def _batch_insert(
    request: Request,
    session: AsyncSessionDep,
    batch_insert_body: BatisBatchInsertBody,
  ):
    return await batis_batch_insert(
      session=session,
      module_config=batis_service.module_config,
      user=request.state.user,
      batch_insert_body=batch_insert_body,
      auto_commit=True,
    )

  @router.post('/update')
  async def _update(
    request: Request,
    session: AsyncSessionDep,
    update_body: BatisUpdateBody,
  ):
    return await batis_update(
      session=session,
      module_config=batis_service.module_config,
      user=request.state.user,
      update_body=update_body,
      auto_commit=True,
    )

  @router.post('/batchUpdate')
  async def _batch_update(
    request: Request,
    session: AsyncSessionDep,
    batch_update_body: BatisBatchUpdateBody,
  ):
    return await batis_batch_update(
      session=session,
      module_config=batis_service.module_config,
      user=request.state.user,
      batch_update_body=batch_update_body,
      auto_commit=True,
    )

  @router.post('/delete')
  async def _delete(
    request: Request,
    session: AsyncSessionDep,
    delete_body: BatisDeleteBody,
  ):
    return await batis_delete(
      session=session,
      module_config=batis_service.module_config,
      user=request.state.user,
      delete_body=delete_body,
    )

  app.include_router(router)
