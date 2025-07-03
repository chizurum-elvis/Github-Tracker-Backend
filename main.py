from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
import os
from dotenv import load_dotenv
from auth import router as auth_router

# Load env variables
load_dotenv()

app = FastAPI(title="GitHub Tracker API Project")

# Validate frontend URL
frontend_url = os.getenv("FRONTEND_URL")
if not frontend_url:
    raise RuntimeError("FRONTEND_URL is not set in the .env file")

# CORS middleware (needed if frontend fetches from another domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,  # Allow cookies to be sent
    allow_methods=["*"],     # Allow all HTTP methods
    allow_headers=["*"],     # Allow all headers
)

# Register auth routes (e.g. /login/github, /logout, /refresh, etc.)
app.include_router(auth_router)

# JWT secret
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set in .env")

# Health root endpoint
@app.get("/")
def root():
    return {"message": "GitHub OAuth Backend running"}

# Authenticated user info endpoint (uses secure cookie)
@app.get("/me")
def get_current_user(request: Request):
    jwt_token = request.cookies.get("access_token")
    if not jwt_token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        payload = jwt.decode(jwt_token, JWT_SECRET, algorithms=["HS256"])
        return {
            "username": payload.get("sub"),
            "name": payload.get("name"),
            "avatar_url": payload.get("avatar_url")
        }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")