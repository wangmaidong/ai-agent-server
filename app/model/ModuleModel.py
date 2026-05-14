import json

from sqlmodel import Field

from app.batis.batis_service.BatisService import BatisService
from app.batis.batis_utils.batis_scheme import BatisModuleColumn, BatisModuleConfig
from app.model.BasicModel import BasicModel
from app.utils.redis_cache import RedisCache


class ModuleModel(BasicModel, table=True):
  __tablename__ = "pl_module"

  label: str | None = Field(default=None, description="模块名称")
  code: str | None = Field(default=None, description="模块标识")
  remarks: str | None = Field(default=None, description="模块备注")
  module_config: str | None = Field(default=None, description="模块配置json信息")


module_cache = RedisCache(
  cache_key="module",
  clazz=ModuleModel,
  clazz_attr=ModuleModel.code,
  ttl=36000000,
  null_ttl=60,
)

module_service = BatisService(
  clazz=ModuleModel,
  base="/module",
  external_columns={
    "moduleConfig": BatisModuleColumn(
      value_type="string",
      convert="json_string"
    ),
  })


async def get_module_config(code: str) -> None | BatisModuleConfig:
  module_dict = await module_cache.get_cache(code)
  if not module_dict:
    return None
  module_config_json_string = module_dict['moduleConfig']
  if not module_config_json_string:
    return None
  return BatisModuleConfig.to_obj(json.loads(module_config_json_string))
