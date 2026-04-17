from pydantic_settings import BaseSettings,SettingsConfigDict
from pydantic import Field
from tomlkit.items import Bool


class EnvSettings(BaseSettings):
  db_host: str = Field(..., env="DB_HOST")
  db_port: str = Field(..., env="DB_PORT")
  db_username: str = Field(..., env="DB_USERNAME")
  db_password: str = Field(..., env="DB_PASSWORD")
  db_database: str = Field(..., env="DB_DATABASE")

  llm_key_local: str = Field(..., env="LLM_KEY_LOCAL")
  llm_key_huoshan: str = Field(..., env="LLM_KEY_HUOSHAN")
  llm_key_bailian: str = Field(..., env="LLM_KEY_BAILIAN")
  llm_key_deepseek: str = Field(..., env="LLM_KEY_DEEPSEEK")

  server_port: int = Field(..., env="SERVER_PORT")
  server_enable_cors: bool = Field(..., env="SERVER_ENABLE_CORS")
  # class Config:
  #   env_file = ".env"
  #   env_file_encoding = "utf-8"
  model_config = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8"
  )


env = EnvSettings()
