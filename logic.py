import firebase_admin as fb
from firebase_admin import credentials
from firebase_admin import firestore

cred = credentials.Certificate("serviceAccountKey.json")
fb.initialize_app(cred)

db = firestore.client()

def add_match(user, score):
    match_ref = (
        db.collection("users")
        .document(user)
        .collection("matches")
        .document()
    )
    match_ref.set({"score": score})
    return match_ref.id