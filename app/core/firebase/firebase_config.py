import os

from firebase_admin import credentials, storage
from dotenv import load_dotenv
import firebase_admin


load_dotenv()

cred = credentials.Certificate(
    os.getenv("FIREBASE_CREDENTIALS_PATH")
)

firebase_admin.initialize_app(cred, {
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET")
})

bucket = storage.bucket()