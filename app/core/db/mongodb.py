from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client: AsyncIOMotorClient = None

def connect_db():
    global client
    client = AsyncIOMotorClient(settings.MONGO_URL)
    print("MongoDB connected!")

def get_database():
    return client[settings.MONGO_DB]

def close_database():
    client.close()
    print("MongoDB connection closed")