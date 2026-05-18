import logging
import re

from fastapi import HTTPException

from app.batis.batis_utils.BatisColumnFormatter import BatisColumnFormatter
from app.batis.batis_utils.batis_scheme import BatisQueryBody, BatisModuleConfig
from app.batis.batis_utils.sql_utils import log_sql, MAX_FILTERS_COUNT, MAX_EXPRESSION_LENGTH
from app.batis.sql_builder.build_query_utils import query_format, format_in, format_in_like, date_format_sql, format_string2array, time_format_sql, datetime_format_sql, validate_filter_expression


def build_query_sql(module_config: BatisModuleConfig, query_body: BatisQueryBody):
  if query_body.filters and (len(query_body.filters) > MAX_FILTERS_COUNT):
    raise HTTPException(400, f"Too many filters")

  if query_body.filter_expression and (len(query_body.filter_expression) > MAX_EXPRESSION_LENGTH):
    raise HTTPException(400, f"Expression too long")

  column_formatter = BatisColumnFormatter(module_config)

  distinct_fields = query_body.distinct_fields

  has_distinct = len(distinct_fields) > 0

  field_sql_list = []
  field_sql_values = []

  # /*---------------------------------------with distinct fields-------------------------------------------*/
  if has_distinct:
    print("has_distinct", distinct_fields)
    if len(distinct_fields) > 10:
      raise HTTPException(status_code=400, detail="Too many distinct fields")
    field_sql_list.append("distinct")
    distinct_field_strings = []
    for item_distinct_field in distinct_fields:
      item_column_info = column_formatter.get_col_by_hump_name(item_distinct_field)
      if not item_column_info:
        raise HTTPException(status_code=400, detail=f"column {item_distinct_field} not found")
      item_field_string = f"{query_format(item_column_info.query, item_column_info.value_type)}"

      if not query_body.only_count:
        item_field_string = f"{item_field_string} as '{item_column_info.hump_name}'"
      distinct_field_strings.append(item_field_string)
    field_sql_list.append(','.join(distinct_field_strings))
  else:
    # /*---------------------------------------without distinct fields-------------------------------------------*/
    field_strings = []
    for hump_name in module_config.columns.keys():
      item_column_info = column_formatter.get_col_by_hump_name(hump_name)
      if not item_column_info:
        raise HTTPException(status_code=500, detail=f"column {hump_name} not found")
      field_strings.append(f"{query_format(item_column_info.query, item_column_info.value_type)} as '{item_column_info.hump_name}'")
    field_sql_list.append(','.join(field_strings))

  from_sql_list = ['from']
  from_sql_values = []

  from_sql_list.append(f"{module_config.table_name} t1")

  # /*---------------------------------------join config-------------------------------------------*/
  join_config = module_config.join_config or []
  if len(join_config):
    for item_join_config in join_config:
      item_join_config_type = item_join_config.type
      if item_join_config_type != 'right join' and item_join_config_type != 'left join' and item_join_config_type != 'join':
        raise ValueError(f"Can't recognise join type:{item_join_config_type}")

      from_sql_list.append(f"{item_join_config_type} {item_join_config.table} {item_join_config.alia} on {item_join_config.on}")

  # /*---------------------------------------filters-------------------------------------------*/
  filter_sql_list = []
  filter_sql_values = []

  query_config_filters = query_body.filters

  if len(query_config_filters):
    for index, item_filter in enumerate(query_config_filters):
      if item_filter.id is None:
        item_filter.id = f"_{index}"
    filter_expression = query_body.filter_expression or ' and '.join(item.id for item in query_config_filters)
    filter_expression = re.sub(r'\s+(并且|&&)\s+', ' and ', filter_expression)
    filter_expression = re.sub(r'\s+(或者|\|\|)\s+', ' or ', filter_expression)

    id_2_filter = {item.id: item for item in query_config_filters}
    valid_ids = set(id_2_filter.keys())
    if not validate_filter_expression(filter_expression, valid_ids):
      raise HTTPException(400, "Invalid filter expression")

    def replace_func(match):
      full_match = match.group(0)
      filter_id = full_match

      if filter_id.lower() in ('and', 'or', 'not'):
        return filter_id.lower()

      filter_info = id_2_filter.get(filter_id, None)

      if filter_info is None:
        logging.error(f"filter id {filter_id} not found")
        raise HTTPException(status_code=400, detail="Invalid filter id")

      filter_field = filter_info.field
      item_column = column_formatter.get_col_by_hump_name(filter_field)

      if item_column is None:
        logging.error(f"filter field {filter_field} not found")
        raise HTTPException(status_code=400, detail="Invalid filter field")

      filter_type = filter_info.type or item_column.value_type or 'string'
      value = filter_info.value
      filter_operator = filter_info.operator
      query = item_column.query

      return FilterHandler.handle(filter_type, filter_operator, query, value, filter_sql_values)

    new_filter_expression = re.sub(r'[a-zA-Z0-9_-]+', replace_func, filter_expression)

    filter_sql_list.extend(['where', new_filter_expression])

  sqls = []
  values = []

  # /*---------------------------------------onlyCount-------------------------------------------*/
  query_config_only_count = query_body.only_count

  if query_config_only_count:
    if not has_distinct:
      sqls.append("select count(0) as total")
    else:
      sqls.append(f"select count( {' '.join(field_sql_list)} ) as total")
      values.extend(field_sql_values)

    sqls.extend(from_sql_list)
    values.extend(from_sql_values)

    sqls.extend(filter_sql_list)
    values.extend(filter_sql_values)
  else:
    # /*---------------------------------------not onlyCount-------------------------------------------*/
    sqls.append('select')

    sqls.extend(field_sql_list)
    values.extend(field_sql_values)

    sqls.extend(from_sql_list)
    values.extend(from_sql_values)

    sqls.extend(filter_sql_list)
    values.extend(filter_sql_values)

    # /*---------------------------------------orders-------------------------------------------*/
    def get_sort_sql_value():
      sort_sql_list = []
      sort_sql_values = []

      query_config_orders = query_body.orders
      query_config_orders = query_config_orders if isinstance(query_config_orders, list) else [query_config_orders]
      if len(query_config_orders) > 5:
        raise HTTPException(status_code=400, detail=f"{module_config.table_name} can't sort more than 5 fields")

      if len(query_config_orders) > 0:
        sort_sql_list.append("order by")
        temp_list = []

        for sort_item in query_config_orders:
          sn = ''
          sc = ''

          if isinstance(sort_item, str):
            sn = sort_item
            sc = 'desc'
          else:
            sn = sort_item.field
            sc = 'desc' if sort_item.desc else 'asc'

          column_item = column_formatter.get_col_by_hump_name(sn)

          if column_item is None:
            raise HTTPException(status_code=400, detail=f"Can't sort table {module_config.table_name} with field: {sn}")
          else:
            temp_list.append(f"{column_item.query} {sc}")

        sort_sql_list.append(', '.join(temp_list))
      return (sort_sql_list, sort_sql_values)

    sort_sql_list, sort_sql_values = get_sort_sql_value()

    sqls.extend(sort_sql_list)
    values.extend(sort_sql_values)

  query_config_all = query_body.all

  if not query_config_all and not query_config_only_count:
    offset = query_body.page * query_body.page_size
    size = query_body.page_size + 1
    sqls.append("limit ?,?")
    values.extend([offset, size])

  sql = ' '.join(sqls)
  log_sql(sql, values)
  sql = sql.replace("?", "%s")

  return sql, values


class FilterHandler:
  @staticmethod
  def handle(filter_type, filter_operator, query, value, value_list):
    handler = FilterHandler._HANDLERS.get(filter_type)
    if not handler:
      raise ValueError(f"{filter_type} is not supported")
    return handler(filter_operator, query, value, value_list)

  @staticmethod
  def _handle_string(op, query, value, value_list):
    if op in ('>', '>=', '<', '<='):
      raise HTTPException(400, detail=f"Operator '{op}' is not supported for string type")
    return FilterHandler._common_ops(op, query, value, value_list, format_func=None)

  @staticmethod
  def _handle_number(op, query, value, value_list):
    return FilterHandler._common_ops(op, query, value, value_list, format_func=None)

  @staticmethod
  def _handle_date(op, query, value, value_list):
    return FilterHandler._datetime_like_ops(op, query, value, value_list, date_format_sql)

  @staticmethod
  def _handle_time(op, query, value, value_list):
    return FilterHandler._datetime_like_ops(op, query, value, value_list, time_format_sql)

  @staticmethod
  def _handle_datetime(op, query, value, value_list):
    return FilterHandler._datetime_like_ops(op, query, value, value_list, datetime_format_sql)

  @staticmethod
  def _common_ops(op, query, value, value_list, format_func):
    handlers = {
      '=': lambda: (value_list.append(value), f"{query} = ?")[1],
      '!=': lambda: (value_list.append(value), f"{query} != ?")[1],
      '~': lambda: (value_list.append(f"%{value}%"), f"{query} like ?")[1],
      '>': lambda: (value_list.append(value), f"{query} > ?")[1],
      '>=': lambda: (value_list.append(value), f"{query} >= ?")[1],
      '<': lambda: (value_list.append(value), f"{query} < ?")[1],
      '<=': lambda: (value_list.append(value), f"{query} <= ?")[1],
      'in': lambda: format_in(value, query, False, value_list),
      'not in': lambda: format_in(value, query, True, value_list),
      'in like': lambda: format_in_like(value, query, False, value_list),
      'not in like': lambda: format_in_like(value, query, True, value_list),
      'is null': lambda: f"{query} is null",
      'is not null': lambda: f"{query} is not null",
    }
    handler = handlers.get(op)
    if not handler:
      raise ValueError(f"{op} is not supported")
    return handler()

  @staticmethod
  def _datetime_like_ops(op, query, value, value_list, format_func):
    def eq_like():
      value_list.append(value)
      return f"{format_func(query)} = ?"

    def neq():
      value_list.append(value)
      return f"{format_func(query)} != ?"

    def gt():
      value_list.append(value)
      return f"{query} > ?"

    def gte():
      value_list.append(value)
      return f"{query} >= ?"

    def lt():
      value_list.append(value)
      return f"{query} < ?"

    def lte():
      value_list.append(value)
      return f"{query} <= ?"

    def in_like(not_in):
      v_list = format_string2array(value)
      value_list.extend(v_list)
      return f"{format_func(query)} {'not ' if not_in else ''}in ({','.join('?' for _ in v_list)})"

    handlers = {
      '=': eq_like,
      '~': eq_like,
      '!=': neq,
      '>': gt,
      '>=': gte,
      '<': lt,
      '<=': lte,
      'in': lambda: in_like(False),
      'in like': lambda: in_like(False),
      'not in': lambda: in_like(True),
      'not in like': lambda: in_like(True),
      'is null': lambda: f"{query} is null",
      'is not null': lambda: f"{query} is not null",
    }
    handler = handlers.get(op)
    if not handler:
      raise ValueError(f"{op} is not supported")
    return handler()

  _HANDLERS = {
    "string": _handle_string,
    "number": _handle_number,
    "date": _handle_date,
    "time": _handle_time,
    "datetime": _handle_datetime,
  }
