from pydantic_settings import BaseSettings
from pydantic import Field


class EnvSettings(BaseSettings):
  db_host: str = Field(..., env="DB_HOST")
  db_port: str = Field(..., env="DB_PORT")
  db_username: str = Field(..., env="DB_USERNAME")
  db_password: str = Field(..., env="DB_PASSWORD")
  db_database: str = Field(..., env="DB_DATABASE")

  redis_host: str = Field(..., env="REDIS_HOST")
  redis_port: str = Field(..., env="REDIS_PORT")
  redis_password: str = Field(..., env="REDIS_PASSWORD")
  redis_db: str = Field(..., env="REDIS_DB")

  llm_key_local: str = Field(..., env="LLM_KEY_LOCAL")
  llm_key_huoshan: str = Field(..., env="LLM_KEY_HUOSHAN")
  llm_key_bailian: str = Field(..., env="LLM_KEY_BAILIAN")
  llm_key_deepseek: str = Field(..., env="LLM_KEY_DEEPSEEK")

  server_port: int = Field(..., env="SERVER_PORT")
  server_enable_cors: bool = Field(..., env="SERVER_ENABLE_CORS")
  server_file_save_path: str = Field(..., env='SERVER_FILE_SAVE_PATH')
  server_file_public_path: str = Field(..., env='SERVER_FILE_PUBLIC_PATH')
  server_verify_path: str = Field(..., env='SERVER_VERIFY_PATH')
  server_login_path: str = Field(..., env='SERVER_LOGIN_PATH')
  server_verify_pwd: bool = Field(..., env='SERVER_VERIFY_PWD')

  jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
  jwt_algorithm: str = Field(..., env="JWT_ALGORITHM")
  jwt_access_token_expire_seconds: int = Field(..., env="JWT_ACCESS_TOKEN_EXPIRE_SECONDS")
  jwt_refresh_token_expire_seconds: int = Field(..., env="JWT_REFRESH_TOKEN_EXPIRE_SECONDS")
  jwt_global_enable: bool = Field(..., env="JWT_GLOBAL_ENABLE")
  jwt_white_list: str = Field(..., env="JWT_WHITE_LIST")

  class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"


env = EnvSettings()
