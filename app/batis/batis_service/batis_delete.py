import traceback

from fastapi import HTTPException
from fastapi.logger import logger

from app.batis.batis_interceptors.BatisInterceptorManager import batis_interceptor_manager
from app.batis.sql_builder.build_delete_sql import build_delete_sql
from app.model.UserModel import PublicUser

from app.batis.batis_utils.batis_scheme import BatisDeleteBody, BatisModuleConfig, BatisDebugMeta, BatisDeleteResponse
from app.utils.mysql_utils import AsyncSessionDep


async def batis_delete(
  session: AsyncSessionDep,
  delete_body: BatisDeleteBody,
  module_config: BatisModuleConfig,
  user: PublicUser | None = None,
  debug_data: list[BatisDebugMeta] | None = None,
  auto_commit: bool = True,
) -> BatisDeleteResponse:
  if not delete_body.id:
    raise HTTPException(status_code=400, detail="delete item failed, missing id!")

  if debug_data is None:
    debug_data = []

  conn = await session.connection()

  await batis_interceptor_manager.call(
    batis_type='before_delete',
    module=module_config.base,
    session=session,
    delete_body=delete_body,
    user=user,
    debug_data=debug_data,
  )

  try:
    sql, values = build_delete_sql(module_config, delete_body)
    debug_data.append({"sql": sql, "values": values})
    result = await conn.exec_driver_sql(sql, tuple(values))
    if auto_commit:
      await session.commit()
      deleted_rows = result.rowcount
      if deleted_rows >= 1:
        await batis_interceptor_manager.call(
          batis_type='after_delete',
          module=module_config.base,
          session=session,
          delete_body=delete_body,
          user=user,
          debug_data=debug_data,
        )
        return BatisDeleteResponse(affected_rows=deleted_rows)
      else:
        raise HTTPException(status_code=400, detail="delete item failed, no item deleted!")
    else:
      return BatisDeleteResponse(affected_rows=result.rowcount)
  except Exception as e:
    logger.error(f"delete item failed: {e}")
    traceback.print_exc()
    raise e
