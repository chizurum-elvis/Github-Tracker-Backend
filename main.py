from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
import os
import requests
from dotenv import load_dotenv
from auth import router as auth_router

load_dotenv()
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Auth routes
app.include_router(auth_router)

# JWT validation
security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET")

def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

# Protected endpoint
@app.get("/github/private")
def get_private_data(current_user: dict = Depends(get_current_user)):
    github_username = current_user["sub"]
    res = requests.get(f"https://api.github.com/users/{github_username}/repos?visibility=private",
                       headers={"Authorization": f"token {os.getenv('GITHUB_PERSONAL_TOKEN')}"})
    return res.json()