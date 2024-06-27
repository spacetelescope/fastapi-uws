from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings for the application."""

    UWS_STORE: str = "fastapi_uws.stores.InMemoryStore"
    UWS_WORKER: str = "fastapi_uws.workers.BaseUWSWorker"

    MAX_WAIT_TIME: int = 999


settings = Settings()
