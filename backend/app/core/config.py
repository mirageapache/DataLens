from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# ponytail: 專案根的 .env（config.py 在 backend/app/core/ 往上第 3 層）。
# 本機從 backend/ 跑讀得到；docker 內此路徑是 /.env 不存在，
# pydantic 會自動略過檔案、改用 compose 注入的環境變數。搬動檔案層級要同步改 parents 數字。
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    app_name: str = "DataLens API"
    database_url: str
    redis_url: str


settings = Settings()
