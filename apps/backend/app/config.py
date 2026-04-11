from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "sqlite:///./o1agent.db"
    weekly_max_actions: int = 3

    model_config = {"env_file": ".env"}


settings = Settings()
