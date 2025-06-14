import firebase_admin
from firebase_admin import credentials, firestore

_db = None

def init_firebase(json_path: str = 'restaurant-data-backend-firebase-adminsdk-fbsvc-8b7fe2120f (2).json'):
    global _db
    if not firebase_admin._apps:
        cred = credentials.Certificate(json_path)
        firebase_admin.initialize_app(cred)
    _db = firestore.client()
    return _db

def get_firestore():
    if _db is None:
        raise ValueError("Firestore has not been initialized. Call init_firebase() first.")
    return _db
