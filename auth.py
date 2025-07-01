import os
import requests
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import RedirectResponse
from jose import jwt, JWTError
from datetime import datetime, timedelta
from redis_client import redis_client
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(tags=["Authentication"])
CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")
BACKEND_URL = os.getenv("BACKEND_URL")
JWT_SECRET = os.getenv("JWT_SECRET")

def generate_jwt(username: str, name: str, avatar_url: str):
    payload = {
        "sub": username,
        "name": name,
        "avatar_url": avatar_url,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

@router.get("/login/github")
def github_login():
    BACKEND_URL = os.getenv("BACKEND_URL")
    CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    if not BACKEND_URL:
        raise HTTPException(500, "BACKEND_URL is not set in the environment variables")
    if not CLIENT_ID:
        raise HTTPException(500, "GITHUB_CLIENT_ID is not set in the environment variables")

    redirect_uri = f"https://github-tracker-backend-5bu3.onrender.com/auth/github/callback"
    url = f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={redirect_uri}&scope=repo"
    return RedirectResponse(url)

@router.get("/auth/github/callback")
def github_callback(code: str):
    try:
        token_res = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code
            },
            headers={"Accept": "application/json"}
        )
        token_res.raise_for_status()
        access_token = token_res.json().get("access_token")
        print("GitHub access_token response:", token_res.json())
        if not access_token:
            raise HTTPException(400, "Missing GitHub token")

        user_res = requests.get("https://api.github.com/user", headers={
            "Authorization": f"Bearer {access_token}"
        })
        user_res.raise_for_status()
        user = user_res.json()
        username = user["login"]

        redis_client.set(username, access_token)
        token = generate_jwt(username, user.get("name"), user.get("avatar_url"))
        return RedirectResponse(f"{FRONTEND_URL}?token={token}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/github/private")
def get_private_repos(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid token")
    token = auth_header.split()[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload["sub"]
        access_token = redis_client.get(username)
        if not access_token:
            raise HTTPException(401, "No GitHub token found")

        res = requests.get(
            "https://api.github.com/user/repos?visibility=private",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        res.raise_for_status()
        return res.json()

    except JWTError:
        raise HTTPException(401, "Invalid token")
    except Exception as e:
        raise HTTPException(500, str(e))

@router.post("/logout")
def logout(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = auth_header.split()[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        redis_client.delete(payload["sub"])
        return {"message": "Logged out successfully"}
    except Exception:
        raise HTTPException(401, "Invalid token")

@router.get("/refresh")
def refresh_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = auth_header.split()[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], options={"verify_exp": False})
        new_token = generate_jwt(payload["sub"], payload.get("name"), payload.get("avatar_url"))
        return {"token": new_token}
    except Exception:
        raise HTTPException(401, "Invalid token")