from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(result.scalar())
        print("Conexión exitosa 🚀")

except Exception as e:
    print("Error de conexión:")
    print(e)