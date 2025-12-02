from fastapi import FastAPI
from app.api.router import router
from app.db.mongodb import connect_db, close_database

app = FastAPI(
    title = "Forecash API",
    description = "API para análisis, predicción y reportes.",
    version = "1.0.0"
)

#Routers 
app.include_router(router, prefix="/api")

#Eventos FastAPI
@app.on_event("startup")
def startup_event():
    connect_db

@app.on_event("shutdown")
def shutdown_event():
    close_database()