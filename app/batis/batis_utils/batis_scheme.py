from typing import Any, TypeVar, Generic
from typing import List as TypingList

from sqlmodel import Field

from app.model.BasicModel import BasicSchema
from app.utils.model_utils import FormattedDecimal


# /*---------------------------------------查询相关-------------------------------------------*/

# https://www.perylliame.cn/general-sql/docs/python/page-query.html

# 查询参数中的排序参数类型
class BatisQueryOrder(BasicSchema):
  field: str = Field(..., description="排序字段")
  desc: bool | None = Field(default=True, description="是否降序")


# 查询参数中的筛选参数类型
class BatiQueryFilter(BasicSchema):
  id: str | None = Field(default=None, description="筛选条件标识，当使用动态查询表达式时不能为空")
  field: str = Field(..., description="字段名")
  value: Any | None = Field(default=None, description="字段值")
  operator: str | None = Field(default="=", description="操作符")
  type: str | None = Field(default=None, description="筛选类型：string,number,date,datetime,time")


# 查询参数类型
class BatisQueryBody(BasicSchema):
  page: int | None = Field(default=0, description="页码")
  page_size: int | None = Field(default=5, ge=1, le=100, description="每页数量")
  only_count: bool | None = Field(default=False, description="是否只返回总数，是则返回符合查询条件的总数，结果为 { total: number }")
  with_count: bool | None = Field(default=False, description="是否一并查询总数，是则返回符合查询条件的总数，结果为 { list:[], total: number, hasNext: boolean }，注意的是默认情况下不查询总数，因为查询总数会增加耗时，增大对数据库的查询压力")
  all: bool | None = Field(default=False, description="是否不分页查询所有数据")

  orders: list[BatisQueryOrder] | None = Field(default=[], description="排序字段")
  filters: list[BatiQueryFilter] | None = Field(default=[], description="筛选条件")

  filter_expression: str | None = Field(default=None, description="动态筛选表达式，比如 f1 or f2 or (f3 and f4)，f1,f2,f3,f4为filters中筛选参数对象的id")
  distinct_fields: list[str] | None = Field(default=[], description="要去重的字段")


# 查询结束数据类型
T = TypeVar('T')


class QueryResponse(BasicSchema, Generic[T]):
  list: TypingList[T] | None = Field(default=None, description="查询结果")
  total: int | None = Field(default=None, description="查询结果总数")
  has_next: bool | None = Field(default=False, description="是否有下一页")


BatisQueryResponse = QueryResponse[dict]

# /*---------------------------------------item-------------------------------------------*/

BatisItemBody = dict


class BatisItemResponse(BasicSchema):
  result: dict | None = Field(default=None, description="查询结果")


# /*---------------------------------------insert-------------------------------------------*/

class BatisInsertBody(BasicSchema):
  row: dict = Field(..., description="新建数据")


class BatisInsertResponse(BasicSchema):
  result: dict | None = Field(default=None, description="新建数据插入成功之后重新查询得到的结果数据")
  affected_rows: int | None = Field(default=None, description="新建数据插入成功之后受影响的行数")


# /*---------------------------------------batch insert-------------------------------------------*/
class BatisBatchInsertBody(BasicSchema):
  rows: list[dict] = Field(..., description="要新建的数据")


class BatisBatchInsertResponse(BasicSchema):
  result: list[dict] | None = Field(default=None, description="新建数据插入成功之后重新查询得到的结果数据")
  affected_rows: int | None = Field(default=None, description="新建数据插入成功之后受影响的行数")


# /*---------------------------------------update-------------------------------------------*/

class BatisUpdateBody(BasicSchema):
  row: dict = Field(..., description="更新的数据")
  update_fields: list[str] | None = Field(default=None, description="要更新的字段")


class BatisUpdateResponse(BasicSchema):
  result: dict | None = Field(default=None, description="更新数据成功之后重新查询得到的结果数据")
  affected_rows: int | None = Field(default=None, description="更新数据成功之后受影响的行数")


# /*---------------------------------------batch update-------------------------------------------*/
class BatisBatchUpdateBody(BasicSchema):
  rows: list[dict] = Field(..., description="要更新的数据")
  update_fields: list[str] | None = Field(default=None, description="要更新的字段")


class BatisBatchUpdateResponse(BasicSchema):
  result: list[dict] | None = Field(default=None, description="更新数据成功之后重新查询得到的结果数据")
  affected_rows: int | None = Field(default=None, description="更新数据成功之后受影响的行数")


# /*---------------------------------------delete-------------------------------------------*/

class BatisDeleteBody(BasicSchema):
  id: list[str] | str | None = Field(default=None, description="删除的id")


class BatisDeleteResponse(BasicSchema):
  affected_rows: int | None = Field(default=None, description="删除数据成功之后受影响的行数")


# /*---------------------------------------module config-------------------------------------------*/

class BatisValidRule(BasicSchema):
  type: str = Field(default="string", description="验证规则类型")  # string,number,date,datetime,time,除此之外还有 email, idcard, phone, qq
  value: Any = Field(default=None, description="验证规则值")
  required: bool = Field(default=False, description="是否必填")
  pattern: str | None = Field(default=None, description="正则表达式字符串")
  min: FormattedDecimal | None = Field(default=None, description="最小值")
  max: FormattedDecimal | None = Field(default=None, description="最大值")
  len: int | None = Field(default=None, description="值固定长度")
  enum: TypingList[str] | None = Field(default=None, description="枚举值")
  message: str | None = Field(default=None, description="验证失败提示信息")


class BatisModuleColumn(BasicSchema):
  value_type: str = Field(..., description="字段值类型")
  query: str | None = Field(default=None, description="字段查询表达式，比如 t2.name")
  convert: str | None = Field(default=None, description="字段值转换类型")
  rules: TypingList[BatisValidRule] | None = Field(default=None, description="字段验证规则")


class BatisModuleJoinConfig(BasicSchema):
  type: str = Field(..., description="关联类型")
  table: str = Field(..., description="关联表名")
  alia: str = Field(..., description="关联表别名")
  on: str = Field(..., description="关联条件")


class BatisModuleConfig(BasicSchema):
  table_name: str = Field(..., description="表名")
  base: str = Field(..., description="模块访问路径")
  columns: dict[str, BatisModuleColumn] = Field(..., description="字段配置")
  join_config: list[BatisModuleJoinConfig] | None = Field(default=[], description="关联配置")
  default_orders: list[BatisQueryOrder] | None = Field(default=[], description="默认排序配置")
  internal_filters: list[BatiQueryFilter] | None = Field(default=[], description="内置筛选条件")
  internal_filter_expression: str | None = Field(default=None, description="内置筛选条件表达式")


# /*---------------------------------------debug-------------------------------------------*/

class BatisDebugMeta(BasicSchema):
  sql: str | None = Field(default=None, description="sql")
  values: list[Any] | None = Field(default=None, description="sql参数")
