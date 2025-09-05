from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import os
from .routers import router

app = FastAPI(title="R2R Close – Dashboard UI (HTMX)")

if os.path.exists("ui/static"):
    app.mount("/static", StaticFiles(directory="ui/static"), name="static")
elif os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(router)
