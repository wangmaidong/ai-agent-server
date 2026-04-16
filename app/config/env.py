from pydantic_settings import BaseSettings
from pydantic import Field
from tomlkit.items import Bool


class EnvSettings(BaseSettings):
  llm_key_local: str = Field(..., env="LLM_KEY_LOCAL")
  llm_key_huoshan: str = Field(..., env="LLM_KEY_HUOSHAN")
  llm_key_bailian: str = Field(..., env="LLM_KEY_BAILIAN")
  llm_key_deepseek: str = Field(..., env="LLM_KEY_DEEPSEEK")

  server_port: int = Field(..., env="SERVER_PORT")
  server_enable_cors: bool = Field(..., env="SERVER_ENABLE_CORS")
  class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"


env = EnvSettings()
