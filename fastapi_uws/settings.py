from importlib import import_module

from pydantic_settings import BaseSettings

from fastapi_uws.stores import BaseUWSStore
from fastapi_uws.workers import BaseUWSWorker


class Settings(BaseSettings):
    """Settings for the application."""

    UWS_STORE: str = "fastapi_uws.stores.InMemoryStore"
    UWS_WORKER: str = "fastapi_uws.workers.BaseUWSWorker"

    MAX_WAIT_TIME: int = 999


def import_string(dotted_path: str):
    """Import a class or function from a dotted path string.

    Args:
        dotted_path: The dotted path to the class or function to import.
    """
    module_path, class_name = dotted_path.rsplit(".", 1)
    module = import_module(module_path)
    return getattr(module, class_name)


app_settings = Settings()

uws_store: BaseUWSStore = import_string(app_settings.UWS_STORE)()
uws_worker: BaseUWSWorker = import_string(app_settings.UWS_WORKER)()
max_wait_time = app_settings.MAX_WAIT_TIME
