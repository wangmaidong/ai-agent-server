import datetime
import traceback

from fastapi import HTTPException
from fastapi.logger import logger

from app.batis.batis_interceptors.BatisInterceptorManager import batis_interceptor_manager
from app.batis.batis_service.batis_item import batis_item
from app.batis.batis_utils.Convertor import ListDataConvertor
from app.batis.batis_utils.batis_scheme import BatisInsertBody, BatisModuleConfig, BatisDebugMeta, BatisInsertResponse
from app.batis.batis_utils.sql_utils import get_value
from app.batis.batis_utils.validate_batis_rules import validate_row
from app.batis.sql_builder.build_insert_sql import build_insert_sql
from app.model.UserModel import PublicUser
from app.utils.mysql_utils import AsyncSessionDep
from app.utils.next_id import next_id


async def batis_insert(
  session: AsyncSessionDep,
  insert_body: BatisInsertBody,
  module_config: BatisModuleConfig,
  user: PublicUser | None = None,
  debug_data: list[BatisDebugMeta] | None = None,
  auto_commit: bool = True,
) -> BatisInsertResponse:
  if debug_data is None:
    debug_data = []

  conn = await session.connection()
  # 需要修改insert_body.row，因为后续生成insert sql时需要传递insert_body作为参数
  row = insert_body.row
  row_id = get_value(row, 'id')

  # 转换数据
  ListDataConvertor(module_config).encode_list_data([row])

  # 校验数据
  is_valid, valid_msg = validate_row(row, module_config)
  if not is_valid:
    raise HTTPException(status_code=400, detail=valid_msg)

  # 自动设置row_id
  if not row_id:
    row['id'] = await next_id()
    row_id = row['id']

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
    batis_type='before_insert',
    module=module_config.base,
    row=insert_body.row,
    session=session,
    user=user,
    debug_data=debug_data,
  )

  try:
    sql, values = build_insert_sql(module_config, insert_body)
    debug_data.append({"sql": sql, "values": values})
    result = await conn.exec_driver_sql(sql, tuple(values))

    if not auto_commit:
      # 不自动提交事务，result为None，需要自行提交事务然后查询最新结果
      return BatisInsertResponse(affected_rows=result.rowcount, result=None)

    # 自动提交事务
    await session.commit()

    item_result = await batis_item(
      session,
      item_body={"id": row_id},
      module_config=module_config,
      user=user,
      debug_data=debug_data,
    )
    item_dict = item_result.result

    if not item_dict:
      logger.error(f"insert failed: {insert_body}")
      raise HTTPException(status_code=500, detail="insert item failed, item not found!")

    await batis_interceptor_manager.call(
      batis_type='after_insert',
      module=module_config.base,
      row=item_dict,
      session=session,
      user=user,
      debug_data=debug_data,
    )

    return BatisInsertResponse(
      result=item_dict,
      affected_rows=result.rowcount,
    )
  except Exception as err:
    traceback.print_exc()
    logger.error(f"insert failed: {insert_body}")
    raise err
