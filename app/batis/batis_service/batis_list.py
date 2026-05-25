import traceback
from datetime import datetime, date

from fastapi.logger import logger

from app.batis.batis_interceptors.BatisInterceptorManager import batis_interceptor_manager
from app.batis.batis_utils.batis_scheme import BatisQueryBody, BatisModuleConfig, BatisDebugMeta, BatisQueryResponse
from app.batis.batis_utils.process_default_query_body import process_default_query_body
from app.batis.batis_utils.Convertor import ListDataConvertor
from app.batis.sql_builder.build_query_sql import build_query_sql
from app.batis.batis_utils.sql_utils import get_value
from app.model.UserModel import PublicUser
from app.utils.model_utils import format_datetime_to_string, format_date_to_string
from app.utils.mysql_utils import AsyncSessionDep


async def batis_list(
  session: AsyncSessionDep,
  query_body: BatisQueryBody,
  module_config: BatisModuleConfig,
  user: PublicUser | None = None,
  debug_data: list[BatisDebugMeta] | None = None,
) -> BatisQueryResponse:
  if debug_data is None:
    debug_data = []

  conn = await session.connection()

  module_config, query_body = process_default_query_body(module_config, query_body)

  await batis_interceptor_manager.call(
    batis_type='before_list',
    module=module_config.base,
    query_body=query_body,
    session=session,
    user=user
  )

  sql, values = build_query_sql(module_config, query_body)

  try:

    debug_data.append({"sql": sql, "values": values})
    result = await conn.exec_driver_sql(sql, tuple(values))
    result = [dict(row._mapping) for row in result]

    # 将 datetime, date类型的字段值转化成字符串
    for row in result:
      for k, v in row.items():
        if isinstance(v, datetime):
          row[k] = format_datetime_to_string(v)
        elif isinstance(v, date):
          row[k] = format_date_to_string(v)

    ListDataConvertor(module_config).decode_list_data(result)

    await batis_interceptor_manager.call(
      batis_type='after_list',
      module=module_config.base,
      rows=result,
      session=session,
      user=user
    )

    if query_body.only_count:
      if not result:
        return BatisQueryResponse(total=0, list=None)
      return BatisQueryResponse(total=int(result[0]['total']), list=None)
    else:
      has_next = False if get_value(query_body, 'all', False) else len(result) == (query_body.page_size + 1)
      if has_next:
        result.pop()

      count_query_body = query_body.model_copy()
      count_query_body.only_count = True
      count_result = await batis_list(
        session,
        query_body=count_query_body,
        module_config=module_config,
        debug_data=debug_data,
        user=user
      ) if query_body.with_count else {}

      return BatisQueryResponse(
        has_next=has_next,
        total=count_result.total if query_body.with_count else None,
        list=result
      )
  except Exception as err:
    traceback.print_exc()
    logger.error(f"batis query failed: {query_body}")
    raise err
