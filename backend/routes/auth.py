from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional
import sqlite3
import bcrypt
from datetime import datetime, timedelta
import jwt
import os
import re
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/auth", tags=["auth"])

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "memory", "auth.db")
# For Render, use in-memory database (free tier has no persistent storage)
if os.path.exists('/opt/render/project'):
    DB_PATH = ':memory:'


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    # Ensure directory exists (only for local development)
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir) and not DB_PATH.startswith('/tmp'):
        os.makedirs(db_dir, exist_ok=True)
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# Initialize database on module load
init_db()


class UserRegister(BaseModel):
    email: str
    username: str
    password: str

    @classmethod
    def validate_email(cls, v):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    created_at: str


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return dict(user)


@router.post("/register", response_model=UserResponse)
async def register(user: UserRegister):
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if email already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check if username already exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (user.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Hash password and create user
    password_hash = hash_password(user.password)
    cursor.execute(
        "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
        (user.email, user.username, password_hash)
    )
    conn.commit()
    
    # Get the created user
    cursor.execute("SELECT * FROM users WHERE email = ?", (user.email,))
    user_data = dict(cursor.fetchone())
    conn.close()
    
    return {
        "id": user_data["id"],
        "email": user_data["email"],
        "username": user_data["username"],
        "created_at": user_data["created_at"]
    }


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (form_data.username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE email = ?", (form_data.username,))
    conn.commit()
    conn.close()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "username": user["username"]},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"]
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "username": current_user["username"],
        "created_at": current_user["created_at"]
    }
