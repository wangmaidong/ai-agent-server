import datetime
import traceback

from fastapi import HTTPException
from fastapi.logger import logger

from app.batis.batis_interceptors.BatisInterceptorManager import batis_interceptor_manager
from app.batis.batis_service.batis_list import batis_list
from app.batis.batis_utils.Convertor import ListDataConvertor
from app.batis.batis_utils.batis_scheme import BatisInsertBody, BatisModuleConfig, BatisDebugMeta, BatisBatchInsertResponse, BatisBatchInsertBody, BatisQueryBody, BatiQueryFilter
from app.batis.batis_utils.sql_utils import get_value
from app.batis.batis_utils.validate_batis_rules import validate_row
from app.batis.sql_builder.build_insert_sql import build_insert_sql
from app.model.UserModel import PublicUser
from app.utils.mysql_utils import AsyncSessionDep
from app.utils.next_id import next_id


async def batis_batch_insert(
  session: AsyncSessionDep,
  batch_insert_body: BatisBatchInsertBody,
  module_config: BatisModuleConfig,
  user: PublicUser | None = None,
  debug_data: list[BatisDebugMeta] | None = None,
  auto_commit: bool = True,
) -> BatisBatchInsertResponse:
  if debug_data is None:
    debug_data = []

  rows = batch_insert_body.rows

  if not rows:
    raise HTTPException(status_code=400, detail="batch insert failed, no rows provided!")

  conn = await session.connection()

  # 转换数据
  ListDataConvertor(module_config).encode_list_data(rows)

  for row in rows:
    # 校验数据
    is_valid, valid_msg = validate_row(row, module_config)
    if not is_valid:
      raise HTTPException(status_code=400, detail=valid_msg)

  missing_id_rows = [row for row in rows if not get_value(row, 'id')]
  new_id_list = None if not missing_id_rows else await next_id(len(missing_id_rows))
  if new_id_list:
    for row, new_id in zip(missing_id_rows, new_id_list):
      row['id'] = new_id

  for row in rows:
    # 自动设置创建时间
    if not get_value(row, 'createdAt', None):
      row['createdAt'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 自动设置更新时间
    if not get_value(row, 'updatedAt', None):
      row['updatedAt'] = row['createdAt']
    # 自动设置创建人
    if user:
      row['createdBy'] = user.id
      row['updatedBy'] = user.id

  await batis_interceptor_manager.call(
    batis_type='before_batch_insert',
    module=module_config.base,
    rows=rows,
    session=session,
    user=user,
    debug_data=debug_data,
  )

  try:
    total_affected_rows = 0
    for row in rows:
      insert_body = BatisInsertBody(row=row)
      sql, values = build_insert_sql(module_config, insert_body)
      debug_data.append({"sql": sql, "values": values})
      result = await conn.exec_driver_sql(sql, tuple(values))
      total_affected_rows += result.rowcount

    if not auto_commit:
      # 不自动提交事务，result为None，需要自行提交事务然后查询最新结果
      return BatisBatchInsertResponse(affected_rows=total_affected_rows, result=None)

    # 自动提交事务
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
      logger.error(f"batch insert failed: {batch_insert_body}")
      raise HTTPException(status_code=500, detail="batch insert failed!")

    await batis_interceptor_manager.call(
      batis_type='after_batch_insert',
      module=module_config.base,
      rows=item_list,
      session=session,
      user=user,
      debug_data=debug_data,
    )

    return BatisBatchInsertResponse(
      result=item_list,
      affected_rows=total_affected_rows,
    )
  except Exception as err:
    traceback.print_exc()
    logger.error(f"batch insert failed: {batch_insert_body}")
    raise err
