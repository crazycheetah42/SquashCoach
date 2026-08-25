import os
import json
import re
import requests
import secrets
import webbrowser
import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from http.server import BaseHTTPRequestHandler, HTTPServer
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

        creds = _run_google_oauth_flow()

        with open(TOKEN_CACHE_FILE, "w") as token_file:
            token_file.write(creds.to_json())

    return _firebase_user_from_credentials(creds)


def _run_google_oauth_flow():
    client_config = json.loads(CLIENT_SECRETS_FILE.read_text())
    installed_config = client_config["installed"]
    state = secrets.token_urlsafe(32)
    callback_data = {}

    class OAuthCallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            callback_data.update(parse_qs(urlparse(self.path).query))
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Sign-in complete</h2><p>You can close this window.</p>")

        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), OAuthCallbackHandler)
    redirect_uri = f"http://localhost:{server.server_port}/"
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": installed_config["client_id"],
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    })

    webbrowser.open(auth_url)
    server.handle_request()
    server.server_close()

    if callback_data.get("state", [None])[0] != state:
        raise RuntimeError("Google authentication returned an invalid state.")
    if "error" in callback_data:
        raise RuntimeError(f"Google authentication failed: {callback_data['error'][0]}")
    if "code" not in callback_data:
        raise RuntimeError("Google authentication did not return an authorization code.")

    response = requests.post(
        installed_config["token_uri"],
        data={
            "code": callback_data["code"][0],
            "client_id": installed_config["client_id"],
            "client_secret": installed_config["client_secret"],
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    response.raise_for_status()
    token_data = response.json()

    creds = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data.get("refresh_token"),
        token_uri=installed_config["token_uri"],
        client_id=installed_config["client_id"],
        client_secret=installed_config["client_secret"],
        scopes=SCOPES,
    )
    return creds


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


def summarize_matches_by_month(matches):
    """Group match game results by calendar month for the performance graph."""
    monthly = {}

    for match in matches:
        try:
            summary = summarize_score(match["score"])
        except (AttributeError, TypeError, ValueError):
            continue

        created_at = match.get("created_at")
        month_key = created_at.strftime("%Y-%m") if created_at else "unknown"
        month = monthly.setdefault(
            month_key,
            {
                "label": created_at.strftime("%b %Y") if created_at else "Unknown",
                "wins": 0,
                "losses": 0,
                "matches": 0,
            },
        )
        month["wins"] += summary["wins"]
        month["losses"] += summary["losses"]
        month["matches"] += 1

    return [monthly[key] for key in sorted(monthly)]