import os
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from jose import jwt

load_dotenv()

router = APIRouter()

CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")
BACKEND_URL = os.getenv("BACKEND_URL")
JWT_SECRET = os.getenv("JWT_SECRET")


@router.get("/login/github")
def github_login():
    redirect_uri = f"{BACKEND_URL}/auth/github/callback"
    github_url = f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={redirect_uri}&scope=repo"
    return RedirectResponse(github_url)


@router.get("/auth/github/callback")
def github_callback(code: str):
    # Exchange code for access token
    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code
    }
    token_res = requests.post(token_url, data=data, headers=headers)
    token_json = token_res.json()
    access_token = token_json.get("access_token")

    if not access_token:
        raise HTTPException(status_code=400, detail="Token exchange failed")

    # Fetch user info
    user_res = requests.get("https://api.github.com/user", headers={
        "Authorization": f"token {access_token}"
    })
    user = user_res.json()

    # (Optional) Generate JWT
    jwt_token = jwt.encode({
        "sub": user["login"],
        "name": user.get("name"),
        "avatar_url": user.get("avatar_url")
    }, JWT_SECRET, algorithm="HS256")

    # Redirect to frontend with JWT
    redirect_with_token = f"{FRONTEND_URL}?token={jwt_token}"
    return RedirectResponse(redirect_with_token)