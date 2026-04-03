import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("firebase_key.json")  # your service account key
firebase_admin.initialize_app(cred)
db = firestore.client()