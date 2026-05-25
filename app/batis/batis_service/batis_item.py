from fastapi import HTTPException

from app.batis.batis_service.batis_list import batis_list
from app.model.UserModel import PublicUser

from app.batis.batis_utils.batis_scheme import BatisModuleConfig, BatisDebugMeta, BatisQueryBody, BatiQueryFilter, BatisItemResponse, BatisItemBody
from app.utils.mysql_utils import AsyncSessionDep


async def batis_item(
  session: AsyncSessionDep,
  item_body: BatisItemBody,
  module_config: BatisModuleConfig,
  user: PublicUser | None = None,
  debug_data: list[BatisDebugMeta] | None = None,
) -> BatisItemResponse:
  """
  根据给定条件查询单条记录

  Args:
    session: 数据库会话
    item_body: 查询条件字典，键为驼峰命名字段名
    module_config: 模块配置
    user: 当前用户信息
    debug_data: 调试数据收集器

  Returns:
    包含 result 字段的字典，未找到时 result 为 None
  """
  if debug_data is None:
    debug_data = []

  target_query_body = BatisQueryBody(
    page=0,
    page_size=1,
    with_count=False,
    only_count=False,
    filters=[]
  )
  for hump_name, value in item_body.items():
    target_query_body.filters.append(BatiQueryFilter(
      field=hump_name,
      value=value,
      operator="="
    ))

  if not target_query_body.filters:
    raise HTTPException(status_code=400, detail="query item failed, missing query body!")

  query_result = await batis_list(
    session=session,
    query_body=target_query_body,
    module_config=module_config,
    debug_data=debug_data,
    user=user,
  )
  result_list = query_result.list or []
  if not result_list:
    return BatisItemResponse(result=None)

  return BatisItemResponse(result=result_list[0])
