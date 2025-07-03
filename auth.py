import os
import requests
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from backend.redis_client import redis_client
from dotenv import load_dotenv

load_dotenv()


router = APIRouter(tags=["Authentication"])

CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
CLIENT_SECRET = os.getenv("GITHUB_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")
BACKEND_URL = os.getenv("BACKEND_URL")
JWT_SECRET = os.getenv("JWT_SECRET")

def generate_jwt(username:str, name:str, avatar_url:str):
    payload = {
        "sub" : username,
        "name" : name,
        "avatar_url" : avatar_url,
        "exp" : datetime.now(datetime.timezone.utc) + timedelta(minutes=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

@router.get("/login/github")
def github_login():
    redirect_uri = f"{BACKEND_URL}/auth/github/callback"
    url = f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={redirect_uri}&scope=repo"
    return RedirectResponse(url)

@router.get("/auth/github/callback")
def github_callback(code:str):
    try:
        token_res = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id" : CLIENT_ID,
            "client_secret" : CLIENT_SECRET,
            "code" : code
        },
        headers={"Accept": "application/json"}
        )
        token_res.raise_for_status()
        access_token = token_res.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Missing Github Token")
        
        user_res = requests.get("https://api.github.com/user", headers={"Authorization": f"Bearer {access_token}"})
        user_res.raise_for_status()
        user = user_res.json()
        username = user["login"]

        redis_client.set(username, access_token, ex=3600)
        token = generate_jwt(username=username, name=user["name"], avatar_url=user["avatar_url"])
        expires = (datetime.utcnow() + timedelta(seconds=3600)).strftime("%a, %d-%b-%Y %H:%M:%S GMT")
        response = RedirectResponse(url=FRONTEND_URL, status_code=302)
        response.set_cookie(key="access_token", value=token, httponly=True, secure=True, samesite="Lax", expires=expires)
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/github/private")
def get_private_repos(request: Request):
    jwt_token = request.cookies.get("access_token")
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        payload = jwt.decode(jwt_token, key=JWT_SECRET, algorithms=["HS256"])
        username = payload.get("sub")
        github_token = redis_client.get(username)
        if not github_token:
            raise HTTPException(status_code=401, detail="No Github token found")
        
        res = requests.get("https://api.github.com/user/repos?visibility=private", headers={"Authorization": f"Bearer {github_token}"})
        res.raise_for_status()
        return res.json()
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/logout")
def logout(request: Request, ):
    jwt_token = request.cookies.get("access_token")
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        payload = jwt.decode(jwt_token, key=JWT_SECRET, algorithms=["HS256"])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        redis_client.delete(username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    response = RedirectResponse(url=FRONTEND_URL, status_code=302)
    response.delete_cookie("access_token")
    return response

@router.get("/refresh")
def refresh_token(request: Request):
    jwt_token = request.cookies.get("access_token")
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        payload = jwt.decode(jwt_token, JWT_SECRET, algorithms=["HS256"], options={"verify_exp": False})

        new_token = generate_jwt(
            sub=payload["sub"],
            name=payload.get("name"),
            avatar_url=payload.get("avatar_url")
        )

        response = JSONResponse(content={"message": "Token refreshed"})
        response.set_cookie(
            key="access_token",
            value=new_token,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=3600  
        )
        return response

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/health/redis")
def check_redis():
    try:
        redis_client.ping()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "details": str(e)}