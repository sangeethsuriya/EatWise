
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime
import random
import re

from src.db.database import get_db
from src.db.models import User, VerificationCode
from src.auth.utils import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

# Models
class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class VerifyCode(BaseModel):
    email: EmailStr
    code: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Helper
def validate_password_strength(password: str):
    """Min 8 chars, 1 number or special char."""
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    if not re.search(r"[0-9!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(status_code=400, detail="Password must contain a number or special character.")

# Endpoints

@router.post("/register")
async def register(user: UserRegister, db: Session = Depends(get_db)):
    # 0. Validate Password
    validate_password_strength(user.password)

    # 1. Check if user exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Create User (Unverified)
    hashed_pw = get_password_hash(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pw, is_verified=False)
    db.add(new_user)
    db.commit()

    # 3. Generate Verification Code
    code = f"{random.randint(100000, 999999)}"
    db_code = VerificationCode(email=user.email, code=code, expires_at=datetime.utcnow())
    db.add(db_code)
    db.commit()

    # 4. Mock Email Send (Console Log)
    print(f"\n📨 [MOCK EMAIL] To: {user.email} | Code: {code}\n")
    
    return {"message": "User registered. Check console for verification code."}

@router.post("/verify")
async def verify(data: VerifyCode, db: Session = Depends(get_db)):
    # 1. Find Code
    record = db.query(VerificationCode).filter(
        VerificationCode.email == data.email,
        VerificationCode.code == data.code
    ).first()
    
    if not record:
        raise HTTPException(status_code=400, detail="Invalid code")
        
    # 2. Verify User
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_verified = True
    db.delete(record) # Cleanup
    db.commit()
    
    return {"message": "Email verified successfully."}

@router.post("/login", response_model=Token)
async def login(user: UserLogin, db: Session = Depends(get_db)):
    # 1. Check User
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
        
    if not db_user.is_verified:
        # Re-send code logic could go here
        raise HTTPException(status_code=400, detail="Email not verified")

    # 2. Generate Token
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}
