import datetime
import traceback

from fastapi import HTTPException
from fastapi.logger import logger

from app.batis.batis_interceptors.BatisInterceptorManager import batis_interceptor_manager
from app.batis.batis_service.batis_item import batis_item
from app.batis.batis_utils.Convertor import ListDataConvertor
from app.batis.batis_utils.batis_scheme import BatisUpdateBody, BatisModuleConfig, BatisDebugMeta, BatisUpdateResponse
from app.batis.batis_utils.sql_utils import get_value
from app.batis.batis_utils.validate_batis_rules import validate_row
from app.batis.sql_builder.build_update_sql import build_update_sql
from app.model.UserModel import PublicUser
from app.utils.mysql_utils import AsyncSessionDep


async def batis_update(
  session: AsyncSessionDep,
  update_body: BatisUpdateBody,
  module_config: BatisModuleConfig,
  user: PublicUser | None = None,
  debug_data: list[BatisDebugMeta] | None = None,
  auto_commit: bool = True,
) -> BatisUpdateResponse:
  if debug_data is None:
    debug_data = []

  conn = await session.connection()
  row = update_body.row
  row_id = get_value(row, 'id')

  if not row_id:
    raise HTTPException(status_code=400, detail="update failed, row id is required!")

  # 转换数据
  ListDataConvertor(module_config).encode_list_data([row])

  # 校验数据
  # UPDATE 场景传 is_partial=True
  is_valid, valid_msg = validate_row(row, module_config, is_partial=True)
  if not is_valid:
    raise HTTPException(status_code=400, detail=valid_msg)

  # 自动设置更新时间
  row['updatedAt'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  # 自动设置创建人
  row['updatedBy'] = user.id if user and user.id else 'unknown'

  await batis_interceptor_manager.call(
    batis_type='before_update',
    module=module_config.base,
    row=update_body.row,
    session=session,
    user=user,
    debug_data=debug_data,
  )

  try:
    sql, values = build_update_sql(module_config, update_body)
    debug_data.append({"sql": sql, "values": values})
    result = await conn.exec_driver_sql(sql, tuple(values))

    if not auto_commit:
      return BatisUpdateResponse(affected_rows=result.rowcount, result=None)

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
      logger.error(f"update failed: {update_body}")
      raise HTTPException(status_code=500, detail=f"update item failed, item not found! {row_id}")

    await batis_interceptor_manager.call(
      batis_type='after_update',
      module=module_config.base,
      row=item_dict,
      session=session,
      user=user,
      debug_data=debug_data,
    )

    return BatisUpdateResponse(
      result=item_dict,
      affected_rows=result.rowcount,
    )
  except Exception as err:
    traceback.print_exc()
    logger.error(f"update failed: {update_body}")
    raise err
