from fastapi import FastAPI
from backend.api import endpoints

app = FastAPI()

app.include_router(endpoints.router)
