import os
import json
import re
import requests
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path
from urllib.parse import urlencode
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


BASE_DIR = Path(__file__).resolve().parent
CLIENT_SECRETS_FILE = BASE_DIR / "client_secret.json"
TOKEN_CACHE_FILE = BASE_DIR / "token.json"
SERVICE_ACCOUNT_FILE = BASE_DIR / "serviceAccountKey.json"
FIREBASE_API_KEY = "AIzaSyCrcrQXDo-YE89CudJau8TFyh1pXeasx5s"
FIREBASE_PROJECT_ID = "squashcoach-505919"

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def load_saved_session():
    creds = None

    if os.path.exists(TOKEN_CACHE_FILE):
        creds = Credentials.from_authorized_user_file(
            TOKEN_CACHE_FILE,
            SCOPES
        )

    if creds and creds.expired and creds.refresh_token:
        print("Refreshing Google login session...")
        creds.refresh(Request())

        with open(TOKEN_CACHE_FILE, "w") as token_file:
            token_file.write(creds.to_json())

    return creds


def login_desktop_user():
    creds = load_saved_session()

    if not creds or not creds.valid:
        print("Opening browser for Google authentication...")

        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES
        )

        creds = flow.run_local_server(port=0)

        with open(TOKEN_CACHE_FILE, "w") as token_file:
            token_file.write(creds.to_json())

    return _firebase_user_from_credentials(creds)


def _firebase_user_from_credentials(creds):
    google_id_token = getattr(creds, "id_token", None)
    google_access_token = getattr(creds, "token", None)

    if google_id_token:
        post_body = urlencode({
            "id_token": google_id_token,
            "providerId": "google.com",
        })
    elif google_access_token:
        post_body = urlencode({
            "access_token": google_access_token,
            "providerId": "google.com",
        })
    else:
        raise RuntimeError(
            "Google authentication did not return a usable token."
        )

    url = (
        "https://identitytoolkit.googleapis.com/v1/"
        f"accounts:signInWithIdp?key={FIREBASE_API_KEY}"
    )

    response = requests.post(
        url,
        json={
            "postBody": post_body,
            "requestUri": "http://localhost",
            "returnSecureToken": True,
            "returnIdpCredential": True,
        },
        timeout=30,
    )

    print(response.text)
    response.raise_for_status()
    if not response.ok:
        print("Firebase response:")
        print(response.text)
        response.raise_for_status()

    firebase_data = response.json()

    firebase_id_token = firebase_data["idToken"]
    firebase_refresh_token = firebase_data["refreshToken"]
    firebase_uid = firebase_data["localId"]

    print("Firebase login successful!")
    print("Firebase UID:", firebase_uid)

    return {
        "uid": firebase_uid,
        "id_token": firebase_id_token,
        "refresh_token": firebase_refresh_token,
        "email": firebase_data.get("email"),
        "display_name": firebase_data.get("displayName"),
        "photo_url": firebase_data.get("photoUrl"),
    }


def get_signed_in_user():
    """Return the saved authenticated user, or None when no session exists."""
    creds = load_saved_session()
    if not creds or not creds.valid:
        return None
    return _firebase_user_from_credentials(creds)


def sign_out_user():
    if os.path.exists(TOKEN_CACHE_FILE):
        os.remove(TOKEN_CACHE_FILE)


def _get_firestore_client():
    try:
        return firestore.client()
    except ValueError:
        firebase_admin.initialize_app(
            credentials.Certificate(SERVICE_ACCOUNT_FILE)
        )
        return firestore.client()


def add_match(user, score):
    uid = user["uid"]
    match_ref = (
        _get_firestore_client()
        .collection("users")
        .document(uid)
        .collection("matches")
        .document()
    )
    match_ref.set({
        "score": score,
        "created_at": firestore.SERVER_TIMESTAMP,
    })
    return match_ref.id


def get_matches(user):
    """Return the user's matches, newest first."""
    matches = []
    match_collection = (
        _get_firestore_client()
        .collection("users")
        .document(user["uid"])
        .collection("matches")
    )

    for document in match_collection.stream():
        data = document.to_dict()
        created_at = data.get("created_at")
        matches.append({
            "id": document.id,
            "score": data.get("score", ""),
            "created_at": created_at,
            "created_at_timestamp": created_at.timestamp() if created_at else 0,
        })

    return sorted(
        matches,
        key=lambda match: match["created_at_timestamp"],
        reverse=True,
    )


def summarize_score(score):
    """Return game wins, losses, and match result for a score string."""
    games = [game.strip() for game in score.split(",") if game.strip()]
    results = []
    for game in games:
        first, second = (
            int(value.strip()) for value in re.fullmatch(r"(\d+)\s*-\s*(\d+)", game).groups()
        )
        results.append("W" if first > second else "L")

    wins = results.count("W")
    losses = results.count("L")
    return {
        "wins": wins,
        "losses": losses,
        "result": "Won" if wins > losses else "Lost",
    }