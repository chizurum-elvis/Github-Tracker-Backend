import os
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from jose import jwt
from datetime import datetime, timedelta

load_dotenv()

router = APIRouter()

CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")
BACKEND_URL = os.getenv("BACKEND_URL")
JWT_SECRET = os.getenv("JWT_SECRET")

# In-memory token store (in production, use a DB or Redis)
token_store = {}


@router.get("/login/github")
def github_login():
    redirect_uri = f"{BACKEND_URL}/auth/github/callback"
    github_url = (
        f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}"
        f"&redirect_uri={redirect_uri}&scope=read:user repo"
    )
    return RedirectResponse(github_url)


@router.get("/auth/github/callback")
def github_callback(code: str):
    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
    }

    token_res = requests.post(token_url, data=data, headers=headers)
    if token_res.status_code != 200:
        raise HTTPException(status_code=502, detail="GitHub token exchange failed")

    access_token = token_res.json().get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Token missing")

    user_res = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    if user_res.status_code != 200:
        raise HTTPException(status_code=502, detail="GitHub user fetch failed")

    user = user_res.json()
    username = user["login"]

    # Store token securely (in-memory for demo)
    token_store[username] = access_token

    expires = datetime.utcnow() + timedelta(minutes=30)
    jwt_token = jwt.encode({
        "sub": username,
        "name": user.get("name"),
        "avatar_url": user.get("avatar_url"),
        "exp": expires
    }, JWT_SECRET, algorithm="HS256")

    return RedirectResponse(f"{FRONTEND_URL}/?token={jwt_token}")


@router.get("/github/private")
def get_private_repos(token: str):
    from jose import JWTError
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload["sub"]
        access_token = token_store.get(username)
        if not access_token:
            raise HTTPException(status_code=401, detail="No GitHub token found")

        res = requests.get(
            "https://api.github.com/user/repos?visibility=private",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return res.json()
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")