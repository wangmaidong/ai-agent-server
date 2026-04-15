from pydantic_settings import BaseSettings
from pydantic import Field


class EnvSettings(BaseSettings):
  server_port: int = Field(..., env="SERVER_PORT")

  class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"


env = EnvSettings()
