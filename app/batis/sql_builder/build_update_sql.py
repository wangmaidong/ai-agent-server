from datetime import datetime

from fastapi import HTTPException

from app.batis.batis_utils.sql_utils import get_value, log_sql, get_value_sql
from app.batis.batis_utils.batis_scheme import BatisModuleConfig, BatisUpdateBody
from app.batis.batis_utils.BatisColumnFormatter import BatisColumnFormatter


# 更新时排除的字段（这些字段不允许在UPDATE操作中被修改）
UPDATE_EXCLUDE_FIELDS = ["id", "createdAt", "createdBy"]


def build_update_sql(module_config: BatisModuleConfig, update_body: BatisUpdateBody):
    # 从更新数据中获取记录ID
    row_id = get_value(update_body.row, "id", None)
    # 默认就是按需更新字段，字典里边出现的字段才会更新
    update_fields = update_body.update_fields or update_body.row.keys()

    # 如果没有提供ID，则抛出异常（更新操作必须指定记录ID）
    if row_id is None:
        raise HTTPException(status_code=400, detail="row_id is None")

    # 创建列格式化器，用于处理字段名映射和列信息
    column_formatter = BatisColumnFormatter(module_config)
    # 初始化SQL语句片段列表
    sqls = [f"update {module_config.table_name} set"]
    # 初始化参数值列表
    values = []

    # 存储SET子句中的字段赋值表达式列表
    field_sql_list = []
    # 遍历所有驼峰命名的字段及其对应的列配置
    for hump_name, column in column_formatter.hump_to_columns.items():
        # 从更新数据中获取当前字段的值
        value = get_value(update_body.row, hump_name, None)

        # 如果字段在排除列表中，则跳过（不更新这些字段）
        if hump_name in UPDATE_EXCLUDE_FIELDS:
            continue

        # 如果列的查询条件不以't1.'开头，则跳过（只处理主表字段）
        if not column.query.startswith("t1."):
            continue

        # 如果指定了要更新的字段列表，且当前字段不在其中，则跳过
        if hump_name != "updatedAt" and hump_name not in update_fields:
            # 如果有指定更新的字段，并且humpName不在这个字段列表中，则不更新这个字段
            continue

        # 如果是updatedAt字段，则自动设置为当前时间
        if hump_name == "updatedAt":
            value = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 生成字段赋值表达式：column_name = ?，并将实际值添加到values列表
        field_sql_list.append(
            f"{column.col_name} = {get_value_sql(value=value, value_type=column.value_type, sql_values=values, )}"
        )

    # 将所有字段赋值表达式用逗号连接，添加到SQL语句中
    sqls.append(", ".join(field_sql_list))
    # 添加WHERE条件，通过ID定位要更新的记录
    sqls.append("where id = ?")
    # 将记录ID添加到参数值列表
    values.append(row_id)

    # 拼接完整的SQL语句
    sql = " ".join(sqls)
    # 记录生成的SQL语句和参数（用于调试）
    log_sql(sql, values)
    # 将占位符从?替换为%s（MySQL的参数化查询格式）
    sql = sql.replace("?", "%s")
    # 返回最终的SQL语句和参数值列表
    return sql, values

if __name__ == "__main__":
  from app.batis.batis_utils.DEMO_MODULE_CONFIG import DEMO_MODULE_CONFIG
  update_dict = {
    "row": {"normalText": "abc", "numberVal": 213, "id": "12345"},
    "update_fields": [
      "normalText"
    ]
  }
  build_update_sql(DEMO_MODULE_CONFIG, BatisUpdateBody.to_obj(update_dict))
