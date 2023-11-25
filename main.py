import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import requests
from dotenv import load_dotenv
import os
from flask import Flask, redirect, request, jsonify, session
import urllib.parse
from datetime import datetime
import json

load_dotenv()  # getting credentials
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
"""dont forget to create an app in spotify developer dash, set the 
credentials from the app in the env"""
SESSION_SECRET = os.getenv("SESSION_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
"""the user should add .env file with credentials"""

app = Flask(__name__)

app.secret_key = SESSION_SECRET

AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1/"


@app.route("/")
def index():
    return "<h1>hi and welcome to spotify playlist genarator\
           click here <a href='/login'>login</a> to login with spotify</h1>"


@app.route("/login")
def login():
    if "access_token" in session:
        """a.k.a logged in already"""
        return redirect("/playlists")

    SCOPE = "user-read-private user-read-email"

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": SCOPE,  # this is the user permissions
        "redirect_uri": REDIRECT_URI,
        "show_dialog": True,
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)


@app.route("/callback")
def callback():
    if "error" in request.args:
        return jsonify({"error": request.args["error"]})
    if "code" in request.args:
        req_body = {
            "code": request.args["code"],
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        res = requests.post(TOKEN_URL, data=req_body)
        token_info = res.json()
        print(f"token info : {token_info}")
        session["access_token"] = token_info["access_token"]
        session["refresh_token"] = token_info["refresh_token"]
        session["expires_at"] = datetime.now().timestamp() + token_info["expires_in"]
        return redirect("/playlists")


def token_expired() -> bool:
    """checks if the token session expires, returns True if yes"""
    return datetime.now().timestamp() >= session["expires_at"]


@app.route("/playlists")
def playlists():
    if not "access_token" in session:
        return redirect("/login")

    if token_expired():
        return redirect("/refresh-token")

    headers = {"Authorization": f"Bearer {session['access_token']}"}
    try:
        response = requests.get(API_BASE + "me/playlists", headers=headers)
        playlists = response.json()
        return jsonify(playlists)
    except:
        return f"something went wrong with {API_BASE+'me',headers}"


@app.route("/refresh-token")
def refresh_token():
    if not "refresh_token" in session:
        return redirect("/login")

    if token_expired():
        """making sure again that the token expired.."""
        req_body = {
            "grant_type": "refresh_token",
            "refresh_token": session["refresh_token"],
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        res = requests.post(TOKEN_URL, data=req_body)
        new_token_info = res.json()
        session["access_token"] = new_token_info["access_token"]
        session["expires_at"] = (
            datetime.now().timestamp() + new_token_info["expires_in"]
        )
    return redirect("/playlists")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
