from importlib import import_module
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from fastapi_uws.stores import BaseUWSStore
from fastapi_uws.workers import BaseUWSWorker

EXPIRY_DAY = 86400  # 1 day in seconds


class StoreSettings(BaseSettings):
    """Settings for the UWS store."""

    default_expiry: int = Field(
        EXPIRY_DAY * 3, description="The default expiry time for jobs and results in the store in seconds."
    )
    max_expiry: int = Field(
        EXPIRY_DAY * 7, description="The maximum expiry time for jobs and results in the store in seconds."
    )

    model_config = SettingsConfigDict(
        description="The configuration for the UWS store.",
        env_prefix="UWS_STORE_",
    )


class WorkerSettings(BaseSettings):
    """Settings for the UWS worker."""

    model_config = SettingsConfigDict(
        description="The configuration for the UWS worker.",
        env_prefix="UWS_WORKER_",
    )


class Settings(BaseSettings):
    """Settings for the application."""

    store_class: str = Field(
        "fastapi_uws.stores.mem_store.InMemoryStore", description="The class to use for the UWS store."
    )
    worker_class: str = Field("fastapi_uws.workers.BaseUWSWorker", description="The class to use for the UWS worker.")

    worker_settings: Annotated[WorkerSettings, Field(default_factory=WorkerSettings)]
    store_settings: Annotated[StoreSettings, Field(default_factory=StoreSettings)]

    model_config = SettingsConfigDict(
        description="The configuration for the application.",
        env_prefix="UWS_",
        cli_parse_args=True,
    )


def import_string(dotted_path: str):
    """Import a class or function from a dotted path string.

    Args:
        dotted_path: The dotted path to the class or function to import.
    """
    module_path, class_name = dotted_path.rsplit(".", 1)
    module = import_module(module_path)
    return getattr(module, class_name)


# TODO: making these a singleton for now for testing purposes
#      this should be refactored to use dependency injection, maybe?
_store_instance = None
_worker_instance = None


def get_store_instance() -> BaseUWSStore:
    """Get an instance of the configured UWS store."""
    global _store_instance
    if _store_instance is None:
        store_class = import_string(app_settings.store_class)
        store_settings = app_settings.store_settings.model_dump()
        _store_instance = store_class(**store_settings)
    return _store_instance


def get_worker_instance() -> BaseUWSWorker:
    """Get an instance of the configured UWS worker."""
    global _worker_instance
    if _worker_instance is None:
        worker_class = import_string(app_settings.worker_class)
        _worker_instance = worker_class()
    return _worker_instance


app_settings = Settings()
