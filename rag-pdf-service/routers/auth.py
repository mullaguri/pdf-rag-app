from fastapi import Body, APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, BaseModel, ConfigDict, EmailStr, Field, field_validator
from typing import Optional
import models
from models import BlacklistedToken, RefreshToken
from database import get_db
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta, timezone
from passlib.context import CryptContext
from models import User
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY =  settings.SECRET_KEY
# https://www.hexhero.com/tools/random-key-generator  or openssl rand -hex 32 on mac/linux
ALGORITHM = settings.ALGORITHM
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# OAuth2 security scheme - exported for use in other routers
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/auth/login")


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, description="The username of the user")
    email: EmailStr = Field(min_length=5, max_length=100, description="The email of the user")
    password: str = Field(min_length=6, max_length=100, description="The password of the user")
    first_name: str = Field(min_length=1, max_length=50, description="The first name of the user")
    last_name: str = Field(min_length=1, max_length=50, description="The last name of the user")

    model_config = {   
        "json_schema_extra": {
            "example": {
                "username": "john_doe",
                "email": "john.doe@example.com",
                "password": "securepassword",
                "first_name": "John",
                "last_name": "Doe"
            }
        }
    }

class BlacklistToken(BaseModel):
    token: str = Field(description="The JWT token to be blacklisted")

    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huX2RvZSIsInJvbGUiOiJzdHVkZW50IiwiZXhwIjoxNjg4ODQ4MDAwfQ.abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567890"
            }   
        }
    }      

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

    model_config = ConfigDict(from_attributes=True)

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(description="The refresh token to obtain a new access token")

    model_config = {
        "json_schema_extra": {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huX2RvZSIsInJvbGUiOiJzdHVkZW50IiwiZXhwIjoxNjg4ODQ4MDAwfQ.abc123def456ghi789jkl012mno345pqr678stu901vwx234yz567890"
            }   
        }
    }

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    first_name: str
    last_name: str

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "username": "john_doe",
                "email": "john.doe@example.com",
                "role": "user",
                "first_name": "John",
                "last_name": "Doe"
            }
        }
    }

    

@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(from_data:OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == from_data.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    
    if not bcrypt_context.verify(from_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_refresh_token(data={"sub": user.username, "role": user.role}, expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))

    token_response = Token(access_token=access_token, refresh_token = refresh_token,  token_type="bearer")

    #Store refresh token in database

    new_refresh_token = RefreshToken(
        user_id=user.id,
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        created_by=user.username,
        updated_by=user.username,
        revoked=False
    )
    db.add(new_refresh_token)
    db.commit()
    
    return token_response

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    # Here you can add expiration time to the token if needed
    expires = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expires})
    to_encode.update({"type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    # Here you can add expiration time to the token if needed
    expires = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expires})
    to_encode.update({"type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
    


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(UserRequest: CreateUserRequest = Body(...), db: Session = Depends(get_db)):
    # Check if username or email already exists
    existing_user = db.query(User).filter((User.username == UserRequest.username) | (User.email == UserRequest.email)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username or email already exists")
    
    # Create new user
    new_user = User(
        username=UserRequest.username,
        email=UserRequest.email,
        hashed_password= bcrypt_context.hash(UserRequest.password),
        role="user",
        created_at=date.today(),
        updated_at=date.today(),
        created_by=UserRequest.username,
        updated_by=UserRequest.username,
        first_name=UserRequest.first_name,
        last_name=UserRequest.last_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"message": "User registered successfully", "user_id": new_user.id}

def get_current_user(token: str = Depends(oauth2_bearer), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: int = payload.get("role")
        if username is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired", headers={"WWW-Authenticate": "Bearer"})   
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    blacklisted = db.query(BlacklistedToken).filter(BlacklistedToken.token == token).first()
    if blacklisted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been logged out — please login again", headers={"WWW-Authenticate": "Bearer"})
    
    
    return {"username": user.username, "email": user.email, "role": user.role, "token": token}

def get_current_user_object(token: str = Depends(oauth2_bearer), db: Session = Depends(get_db)):
    user_dict = get_current_user(token, db)
    user = db.query(User).filter(User.username == user_dict["username"]).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.get("/me", response_model=UserResponse)
def get_user_details(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/logout" , status_code=status.HTTP_200_OK)
def logout(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    access_token = current_user["token"]

    # 1. Blacklist the access token
    blacklisted_token = db.query(BlacklistedToken).filter(BlacklistedToken.token == access_token).first()
    if blacklisted_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Access token is already blacklisted")

    new_blacklist = BlacklistedToken(
        token=access_token,
        blacklisted_on=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        created_by=current_user["username"],
        updated_by=current_user["username"]
    )
    db.add(new_blacklist)

    # 2. Revoke all of the user's refresh tokens
    user = db.query(User).filter(User.username == current_user["username"]).first()
    if user:
        refresh_tokens = db.query(RefreshToken).filter(
            RefreshToken.user_id == user.id, 
            RefreshToken.revoked == False
        ).all()
        for token_record in refresh_tokens:
            token_record.revoked = True
            token_record.updated_at = datetime.now(timezone.utc)
            token_record.updated_by = current_user["username"]

    db.commit()
    
    return {"message": "Logged out successfully. All refresh tokens have been revoked."}

@router.post("/cleanup-expired-tokens", status_code=status.HTTP_200_OK)
def cleanup_expired_tokens(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    current_time = datetime.now(timezone.utc)
    expired_tokens = db.query(BlacklistedToken).filter(BlacklistedToken.blacklisted_on < current_time).all()
    for token in expired_tokens:
        db.delete(token)

    expired_refresh_tokens = db.query(RefreshToken).filter(RefreshToken.expires_at < current_time).all()
    for token in expired_refresh_tokens:
        db.delete(token)
    
    db.commit()
    return {"message": "Expired tokens cleaned up successfully"}


@router.post("/refresh")
def refresh_token(refresh_token_request: RefreshTokenRequest = Body(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token — please login again",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(refresh_token_request.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: int = payload.get("role")
        if username is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has expired — please login again", headers={"WWW-Authenticate": "Bearer"})  
    except JWTError:
        raise credentials_exception
    
    blacklisted_Refresh_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token_request.refresh_token ,RefreshToken.revoked == True).first()

    if blacklisted_Refresh_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Refresh Token is already blacklisted, Login again")
    
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type — expected refresh token", headers={"WWW-Authenticate": "Bearer"}) 
    
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    
    new_access_token = create_access_token(data={"sub": user.username, "role": user.role}, expires_delta=timedelta(minutes=15))
    new_refresh_token = create_refresh_token(data={"sub": user.username, "role": user.role}, expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    return {"access_token": new_access_token, "refresh_token": new_refresh_token, "token_type": "bearer"}





@router.post("/forgot-password")
def forgot_password():
    pass
