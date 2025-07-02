from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os
from dotenv import load_dotenv
from auth import router as auth_router

# Load env variables
load_dotenv()

app = FastAPI()

# Validate frontend URL
frontend_url = os.getenv("FRONTEND_URL")
if not frontend_url:
    raise RuntimeError("FRONTEND_URL is not set in the .env file")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)

# JWT middleware (optional extra protection)
security = HTTPBearer()
JWT_SECRET = os.getenv("JWT_SECRET")


@app.get("/")
def root():
    return {"message": "GitHub OAuth Backend running"}


@app.get("/me")
def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=["HS256"])
        return {"username": payload.get("sub"), "name": payload.get("name"), "avatar_url": payload.get("avatar_url")}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
