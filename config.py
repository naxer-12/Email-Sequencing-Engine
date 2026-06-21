from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_host: str = "mysql"
    db_user: str = "root"
    db_password: str
    db_name: str = "emailengine"

    redis_url: str = "redis://redis:6379"

    kafka_broker: str = "kafka:9092"
    gemini_api_key: str

    smtp_host: str = "live.smtp.mailtrap.io"
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def database_url(self) -> str:
        return f"mysql+pymsql://{self.db_user}:{self.db_password}@{self.db_host}/{self.db_name}"


settings = Settings()
