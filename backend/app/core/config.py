from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

# ponytail: 專案根的 .env（config.py 在 backend/app/core/ 往上第 3 層）。
# 本機從 backend/ 跑讀得到；docker 內此路徑是 /.env 不存在，
# pydantic 會自動略過檔案、改用 compose 注入的環境變數。搬動檔案層級要同步改 parents 數字。
_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"

# 上傳目錄的基準路徑（相對於 backend/）
UPLOAD_ROOT: Path = Path(__file__).resolve().parents[2] / "uploads"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    app_name: str = "DataLens API"
    database_url: str
    redis_url: str
    # CORS_ORIGINS 在 .env / compose 中以逗號分隔字串設定多個來源。
    # 例如：CORS_ORIGINS=http://localhost:4200,https://app.example.com
    # 使用 str 不使用 List[str]，避免 pydantic-settings 嘗試將它預先 JSON 解析。
    cors_origins_raw: str = "http://localhost:4200"

    @property
    def cors_origins(self) -> List[str]:
        """將逗號分隔的 cors_origins_raw 轉為 list 回傳。"""
        return [
            origin.strip()
            for origin in self.cors_origins_raw.split(",")
            if origin.strip()
        ]


settings = Settings()
