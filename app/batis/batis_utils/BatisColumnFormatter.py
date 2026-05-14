from pydantic import Field

from app.batis.batis_utils.batis_scheme import BatisModuleConfig, BatisModuleColumn
from app.batis.batis_utils.sql_utils import to_line


class BatisColumnInfo(BatisModuleColumn):
  """
  batis列信息
  """
  hump_name: str | None = Field(default=None, description="驼峰命名")
  line_name: str | None = Field(default=None, description="下划线命名")
  query: str | None = Field(default=None, description="字段查询表达式，比如 t2.name")
  col_name: str | None = Field(default=None, description="数据库表字段名")

  def __init__(self, hump_name: str, **kwargs):
    super().__init__(**kwargs)
    self.hump_name = hump_name
    self.line_name = to_line(hump_name)
    self.query = self.query or f"t1.{self.line_name}"
    self.col_name = self.query.split('.')[1] if '.' in self.query else None


class BatisColumnFormatter:
  """
  batis列查询器
  """

  def __init__(self, module_config: BatisModuleConfig):
    # 通过驼峰命名找到字段信息
    hump_to_columns = {}
    # 通过下划线命名找到字段信息
    line_to_columns = {}

    for hump_name, col_config in module_config.columns.items():
      col_info = BatisColumnInfo(hump_name=hump_name, **col_config.to_dict())
      hump_to_columns[col_info.hump_name] = col_info
      line_to_columns[col_info.line_name] = col_info

    self.hump_to_columns = hump_to_columns
    self.line_to_columns = line_to_columns

  def get_col_by_hump_name(self, hump_name: str) -> BatisColumnInfo | None:
    return self.hump_to_columns.get(hump_name, None)

  def get_col_by_line_name(self, line_name: str) -> BatisColumnInfo | None:
    return self.line_to_columns.get(line_name, None)
