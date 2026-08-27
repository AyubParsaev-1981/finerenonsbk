import os
from typing import List
from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    bot_token: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    admin_ids: List[int] = []

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @classmethod
    def get_admin_ids(cls) -> List[int]:
        """ADMIN_IDS муҳитидан админлар ID рўйхатини олади."""
        raw_admins = os.getenv("ADMIN_IDS", "")
        if not raw_admins:
            return []
        try:
            return [int(x.strip()) for x in raw_admins.split(",") if x.strip().isdigit()]
        except Exception:
            return []


settings = Settings()
settings.admin_ids = settings.get_admin_ids()
