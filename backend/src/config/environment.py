from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, hide_input_in_errors=True)

    DJANGO_SECRET_KEY: SecretStr = SecretStr("")
    DJANGO_ALLOWED_HOSTS: str = "127.0.0.1,localhost"
    DJANGO_DB_PATH: str = Field(
        default=str(Path(__file__).resolve().parents[3] / "db.sqlite3"),
        min_length=1,
        repr=False,
    )
    DESKTOP_TOKEN: SecretStr = SecretStr("")
