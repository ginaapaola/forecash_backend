from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import router


#DOCUMENTACIÓN SWAGGER
app = FastAPI(
    title = "Forecash API",
    description = "API para análisis, predicción y reportes.",
    version = "1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

#CORS
#origins = [
#    "http://localhost:3000",
#   "http://127.0.0.1:3000",
#]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://forecash-chi.vercel.app/login",
        "https://forecash-ginaapaola-gina-paola-s-projects.vercel.app",
        "https://forecash-dyq30u5bo-gina-paola-s-projects.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Routers 
app.include_router(router, prefix="/api")
