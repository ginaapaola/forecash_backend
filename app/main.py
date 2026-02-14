from fastapi import FastAPI
from app.api.router import router
from app.core.config import settings

app = FastAPI(
    title = "Forecash API",
    description = "API para análisis, predicción y reportes.",
    version = "1.0.0"
)

#Routers 
app.include_router(router, prefix="/api")
