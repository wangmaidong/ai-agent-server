from fastapi import HTTPException

from app.batis.batis_utils.sql_utils import log_sql, MAX_BATCH_DELETE_SIZE
from app.batis.batis_utils.batis_scheme import BatisModuleConfig, BatisDeleteBody


# 构建删除SQL语句
def build_delete_sql(module_config: BatisModuleConfig, delete_body: BatisDeleteBody):
  # 使用属性访问获取表名
  table_name = module_config.table_name

  id = delete_body.id

  if isinstance(id, list):
    # 批量删除场景
    if len(id) > MAX_BATCH_DELETE_SIZE:
      raise HTTPException(400, f"Batch delete size exceeds limit of {MAX_BATCH_DELETE_SIZE}")
    placeholders = ','.join(['?'] * len(id))
    sql = f"delete from {table_name} where id in ({placeholders})"
    values = id
  elif id is not None:
    # 单条删除场景
    sql = f"delete from {table_name} where id = ?"
    values = [id]
  else:
    # id为None的情况，返回空SQL和空值列表
    return "", []

  log_sql(sql, values)
  # 替换占位符为MySQL格式
  sql = sql.replace("?", "%s")
  return sql, values
