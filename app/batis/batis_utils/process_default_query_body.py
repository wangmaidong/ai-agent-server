import copy

from fastapi import HTTPException

from app.batis.batis_utils.batis_scheme import BatisQueryBody, BatisModuleConfig, BatisQueryOrder
from app.utils.next_number_id import next_number_id


def process_default_query_body(module_config: BatisModuleConfig, query_body: BatisQueryBody):
  query_body = copy.deepcopy(query_body)
  module_config = copy.deepcopy(module_config)
  # /*---------------------------------------default orders-------------------------------------------*/
  # 补全默认的排序参数，至少得有一个排序字段
  if not query_body.orders:
    query_body.orders = copy.deepcopy(module_config.default_orders) \
      if module_config.default_orders else [BatisQueryOrder(field="createdAt", desc=True)]

  # /*---------------------------------------query filters-------------------------------------------*/
  # 补全查询参数中的筛选条件的id
  if not query_body.filters:
    query_body.filters = []

  for item in query_body.filters:
    if not item.id:
      item.id = f"f_{next_number_id()}"

  if not query_body.filter_expression and query_body.filters:
    query_body.filter_expression = " and ".join([item.id for item in query_body.filters])

  # /*---------------------------------------internal filters-------------------------------------------*/
  # 补全内置筛选条件
  if module_config.internal_filters:
    # 补全内置筛选条件的id
    for item in module_config.internal_filters:
      if not item.id:
        item.id = f"_{next_number_id()}"
    if not module_config.internal_filter_expression:
      module_config.internal_filter_expression = " and ".join([item.id for item in module_config.internal_filters])

    if query_body.filters:
      user_ids = {f.id for f in query_body.filters}
      internal_ids = {f.id for f in module_config.internal_filters}
      conflict_ids = user_ids & internal_ids
      if conflict_ids:
        raise HTTPException(
          status_code=400,
          detail=f"Filter id conflict: {conflict_ids}"
        )
      # 将内置筛选条件添加到查询参数中
      query_body.filters = [*query_body.filters, *module_config.internal_filters]
      query_body.filter_expression = f"( {query_body.filter_expression} ) and ( {module_config.internal_filter_expression} )"
    else:
      query_body.filters = copy.deepcopy(module_config.internal_filters)
      query_body.filter_expression = module_config.internal_filter_expression

  return module_config, query_body
