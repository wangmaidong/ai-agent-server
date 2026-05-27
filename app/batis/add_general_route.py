from enum import Enum

from fastapi import FastAPI, APIRouter, HTTPException
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
from app.model.ModuleModel import get_module_config
from app.utils.mysql_utils import AsyncSessionDep
from app.utils.path_join import path_join


def add_general_route(app: FastAPI):
  router = APIRouter(tags=['general'])

  @router.post("/list")
  async def _list(
    module: str,
    request: Request,
    session: AsyncSessionDep,
    query_body: BatisQueryBody = BatisQueryBody(),
  ):
    module_config = await get_module_config(module)
    if not module_config:
      raise HTTPException(status_code=404, detail=f"Module {module} not found")
    return await batis_list(
      session=session,
      module_config=module_config,
      user=request.state.user,
      query_body=query_body,
    )

  @router.post('/item')
  async def _item(
    module: str,
    request: Request,
    session: AsyncSessionDep,
    item_body: BatisItemBody,
  ):
    module_config = await get_module_config(module)
    if not module_config:
      raise HTTPException(status_code=404, detail=f"Module {module} not found")
    return await batis_item(
      session=session,
      module_config=module_config,
      user=request.state.user,
      item_body=item_body,
    )

  @router.post('/insert')
  async def _insert(
    module: str,
    request: Request,
    session: AsyncSessionDep,
    insert_body: BatisInsertBody,
  ):
    module_config = await get_module_config(module)
    if not module_config:
      raise HTTPException(status_code=404, detail=f"Module {module} not found")
    return await batis_insert(
      session=session,
      module_config=module_config,
      user=request.state.user,
      insert_body=insert_body,
      auto_commit=True,
    )

  @router.post('/batchInsert')
  async def _batch_insert(
    module: str,
    request: Request,
    session: AsyncSessionDep,
    batch_insert_body: BatisBatchInsertBody,
  ):
    module_config = await get_module_config(module)
    if not module_config:
      raise HTTPException(status_code=404, detail=f"Module {module} not found")
    return await batis_batch_insert(
      session=session,
      module_config=module_config,
      user=request.state.user,
      batch_insert_body=batch_insert_body,
      auto_commit=True,
    )

  @router.post('/update')
  async def _update(
    module: str,
    request: Request,
    session: AsyncSessionDep,
    update_body: BatisUpdateBody,
  ):
    module_config = await get_module_config(module)
    if not module_config:
      raise HTTPException(status_code=404, detail=f"Module {module} not found")
    return await batis_update(
      session=session,
      module_config=module_config,
      user=request.state.user,
      update_body=update_body,
      auto_commit=True,
    )

  @router.post('/batchUpdate')
  async def _batch_update(
    module: str,
    request: Request,
    session: AsyncSessionDep,
    batch_update_body: BatisBatchUpdateBody,
  ):
    module_config = await get_module_config(module)
    if not module_config:
      raise HTTPException(status_code=404, detail=f"Module {module} not found")
    return await batis_batch_update(
      session=session,
      module_config=module_config,
      user=request.state.user,
      batch_update_body=batch_update_body,
      auto_commit=True,
    )

  @router.post('/delete')
  async def _delete(
    module: str,
    request: Request,
    session: AsyncSessionDep,
    delete_body: BatisDeleteBody,
  ):
    module_config = await get_module_config(module)
    if not module_config:
      raise HTTPException(status_code=404, detail=f"Module {module} not found")
    return await batis_delete(
      session=session,
      module_config=module_config,
      user=request.state.user,
      delete_body=delete_body,
    )

  app.include_router(router, prefix="/general/{module}")
