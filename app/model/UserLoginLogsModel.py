from sqlmodel import Field

from app.model.BasicModel import BasicModel


class UserLoginLogsModel(BasicModel, table=True):
  """
  登录日志
  """
  __tablename__ = "pl_user_login_logs"

  host: str = Field(default=None, description="ip地址")
  address: str = Field(default=None, description="地理地址")
