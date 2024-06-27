"""Main module."""

from fastapi import FastAPI

from fastapi_uws.router.uws_router import uws_router

app = FastAPI(
    title="Universal Worker Service (UWS)",
    description="The Universal Worker Service (UWS) pattern defines how to manage asynchronous execution of jobs on a service.",
    version="1.2",
)

app.include_router(uws_router)
