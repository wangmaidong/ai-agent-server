import json

from app.batis.batis_utils.batis_scheme import BatisModuleConfig
from app.batis.batis_utils.sql_utils import get_value


class Convertor:
  """
  Convertor类，用于将数据进行转换。
  """

  def __init__(
    self,
    encode,
    decode,
  ):
    self.encode = encode
    self.decode = decode


# /*---------------------------------------list_string-------------------------------------------*/

# 将字符串数组转化为字符串
def list_string_encoder(val):
  if isinstance(val, list):
    return ",".join(val)
  return val


# 将json字符串转为数组
def list_string_decoder(val):
  if isinstance(val, str):
    return val.split(',')
  elif isinstance(val, list):
    return val
  else:
    raise TypeError("list_string_decoder only support str")


list_string_convertor = Convertor(
  encode=list_string_encoder,
  decode=list_string_decoder
)

# /*---------------------------------------json_string-------------------------------------------*/

json_string_convertor = Convertor(
  encode=lambda val: val if isinstance(val, str) else json.dumps(val, ensure_ascii=False),
  decode=lambda val: json.loads(val) if isinstance(val, str) else val
)

# /*---------------------------------------converts-------------------------------------------*/

CONVER_TYPE_LIST = "list_string"
CONVER_TYPE_JSON = "json_string"

convert_utils = {
  CONVER_TYPE_LIST: list_string_convertor,
  CONVER_TYPE_JSON: json_string_convertor,
  # 兼容旧版本
  "arrayjson": json_string_convertor,
  "arraystring": list_string_convertor,
}


# /*---------------------------------------ListDataConvertor-------------------------------------------*/

class ItemDataConvertor:
  def __init__(self, config: BatisModuleConfig):
    self.convert_columns = [(col_name, col_config) for col_name, col_config in config.columns.items() if col_config.convert]

  def encode_item_data(self, item_data: dict):
    if not len(self.convert_columns):
      return
    for col_name, col_config in self.convert_columns:
      convertor = convert_utils.get(col_config.convert)
      if not convertor:
        raise Exception(f"convert type {col_config.convert} not found")
      col_value = get_value(item_data, col_name)
      if col_value is not None:
        if not isinstance(item_data[col_name], str):
          item_data[col_name] = convertor.encode(col_value)

  def decode_item_data(self, item_data: dict):
    if not len(self.convert_columns):
      return
    for col_name, col_config in self.convert_columns:
      convertor = convert_utils.get(col_config.convert)
      if not convertor:
        raise Exception(f"convert type {col_config.convert} not found")
      col_value = get_value(item_data, col_name)
      if col_value is not None:
        if isinstance(item_data[col_name], str):
          item_data[col_name] = convertor.decode(col_value)


class ListDataConvertor:
  def __init__(self, config: BatisModuleConfig):
    self.item_convertor = ItemDataConvertor(config)

  def encode_list_data(self, list_data: list[dict]):
    if not len(self.item_convertor.convert_columns):
      return
    for item in list_data:
      self.item_convertor.encode_item_data(item)

  def decode_list_data(self, list_data: list[dict]):
    if not len(self.item_convertor.convert_columns):
      return
    for item in list_data:
      self.item_convertor.decode_item_data(item)
