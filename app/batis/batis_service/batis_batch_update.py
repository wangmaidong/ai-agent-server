import datetime
import traceback

from fastapi import HTTPException
from fastapi.logger import logger

from app.batis.batis_interceptors.BatisInterceptorManager import batis_interceptor_manager
from app.batis.batis_service.batis_list import batis_list
from app.batis.batis_utils.Convertor import ListDataConvertor
from app.batis.batis_utils.batis_scheme import BatisModuleConfig, BatisDebugMeta, BatisBatchUpdateResponse, BatisBatchUpdateBody, BatisQueryBody, BatiQueryFilter, BatisUpdateBody
from app.batis.batis_utils.sql_utils import get_value
from app.batis.batis_utils.validate_batis_rules import validate_row
from app.batis.sql_builder.build_update_sql import build_update_sql
from app.model.UserModel import PublicUser
from app.utils.mysql_utils import AsyncSessionDep


async def batis_batch_update(
  session: AsyncSessionDep,
  batch_update_body: BatisBatchUpdateBody,
  module_config: BatisModuleConfig,
  user: PublicUser | None = None,
  debug_data: list[BatisDebugMeta] | None = None,
  auto_commit: bool = True,
) -> BatisBatchUpdateResponse:
  if debug_data is None:
    debug_data = []

  rows = batch_update_body.rows

  if not rows:
    raise HTTPException(status_code=400, detail="batch update failed, no rows provided!")

  for row in rows:
    row_id = get_value(row, 'id')
    if not row_id:
      raise HTTPException(status_code=400, detail="batch update failed, row id is required!")

  conn = await session.connection()

  # 转换数据
  ListDataConvertor(module_config).encode_list_data(rows)

  for row in rows:
    # 校验数据
    # UPDATE 场景传 is_partial=True
    is_valid, valid_msg = validate_row(row, module_config, is_partial=True)
    if not is_valid:
      raise HTTPException(status_code=400, detail=valid_msg)

  for row in rows:
    # 自动设置更新时间
    row['updatedAt'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 自动设置更新人
    if user:
      row['updatedBy'] = user.id

  await batis_interceptor_manager.call(
    batis_type='before_batch_update',
    module=module_config.base,
    rows=rows,
    session=session,
    user=user,
    debug_data=debug_data,
  )

  try:
    total_affected_rows = 0
    for row in rows:
      update_body = BatisUpdateBody(row=row, update_fields=batch_update_body.update_fields)
      sql, values = build_update_sql(module_config, update_body)
      debug_data.append({"sql": sql, "values": values})
      result = await conn.exec_driver_sql(sql, tuple(values))
      total_affected_rows += result.rowcount

    if not auto_commit:
      return BatisBatchUpdateResponse(affected_rows=total_affected_rows, result=None)

    await session.commit()

    item_result = await batis_list(
      session,
      query_body=BatisQueryBody(
        all=True,
        filters=[BatiQueryFilter(id='id', operator='in', field='id', value=[row['id'] for row in rows])]
      ),
      module_config=module_config,
      user=user,
      debug_data=debug_data,
    )
    item_list = item_result.list

    if not item_list or len(item_list) != len(rows):
      logger.error(f"batch update failed: {batch_update_body}")
      raise HTTPException(status_code=500, detail="batch update failed!")

    await batis_interceptor_manager.call(
      batis_type='after_batch_update',
      module=module_config.base,
      rows=item_list,
      session=session,
      user=user,
      debug_data=debug_data,
    )

    return BatisBatchUpdateResponse(
      result=item_list,
      affected_rows=total_affected_rows,
    )
  except Exception as err:
    traceback.print_exc()
    logger.error(f"batch update failed: {batch_update_body}")
    raise err
