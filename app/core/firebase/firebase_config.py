import os
import json
from firebase_admin import credentials, storage
from dotenv import load_dotenv
import firebase_admin

load_dotenv()

firebase_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
if firebase_json:
    cred = credentials.Certificate(json.loads(firebase_json))
else:
    cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))

firebase_admin.initialize_app(cred, {
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET")
})
bucket = storage.bucket()