from app.batis.batis_utils.DEMO_MODULE_CONFIG import DEMO_MODULE_CONFIG
from app.batis.batis_utils.sql_utils import get_value, get_value_sql, log_sql
from app.batis.batis_utils.batis_scheme import BatisModuleConfig, BatisInsertBody
from app.batis.batis_utils.BatisColumnFormatter import BatisColumnFormatter


def build_insert_sql(module_config: BatisModuleConfig, insert_body: BatisInsertBody):
  # 创建列格式化器，用于处理字段名映射和列信息
  column_formatter = BatisColumnFormatter(module_config)
  # 初始化SQL语句片段列表
  sqls = [f"insert into {module_config.table_name}"]
  # 初始化参数值列表
  values = []

  # 存储SQL左侧字段名列表（数据库列名）
  field_sql_left_list = []
  # 存储SQL右侧占位符列表（? 或 %s）
  field_sql_right_list = []
  # 存储实际参数值列表（用于防止SQL注入）
  field_sql_right_values = []

  # 遍历所有驼峰命名的字段及其对应的列配置
  for hump_name, column in column_formatter.hump_to_columns.items():
    # 从插入数据中获取当前字段的值
    value = get_value(insert_body.row, hump_name)

    # 如果值为None，则跳过该字段（不插入空值）
    if value is None:
      continue

    # 如果列的查询条件中不包含't1.'，则跳过（只处理主表字段）
    if not column.query.startswith('t1.'):
      continue

    # 将数据库列名添加到左侧字段列表
    field_sql_left_list.append(column.col_name)
    # 根据值类型生成对应的SQL占位符，并将实际值存入field_sql_right_values
    field_sql_right_list.append(get_value_sql(
      value=value,
      value_type=column.value_type,
      sql_values=field_sql_right_values,
    ))

  # 构建INSERT语句的字段部分：(column1, column2, ...)
  sqls.append(f"( {', '.join(field_sql_left_list)} ) ")
  # 添加VALUES关键字
  sqls.append("values")
  # 构建VALUES部分：(?, ?, ...)
  sqls.append(f"( {', '.join(field_sql_right_list)} )")
  # 将所有参数值合并到values列表中
  values.extend(field_sql_right_values)
  # 拼接完整的SQL语句
  sql = ' '.join(sqls)
  # 记录生成的SQL语句和参数（用于调试）
  log_sql(sql, values)
  # 将占位符从?替换为%s（MySQL的参数化查询格式）
  sql = sql.replace("?", "%s")
  # 返回最终的SQL语句和参数值列表
  return sql, values


if __name__ == "__main__":
  build_insert_sql(DEMO_MODULE_CONFIG, BatisInsertBody.to_obj({"row": {"normalText": "abc", "numberVal": 213}}))
