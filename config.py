import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# .env файлини юклаш
load_dotenv()


class Settings(BaseSettings):
    bot_token: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
