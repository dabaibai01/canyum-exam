from pydantic import BaseModel
from datetime import datetime

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    password: str
    real_name: str
    phone: str | None = None
    department: str | None = None
    position: str | None = None

class UserOut(BaseModel):
    id: int
    username: str
    real_name: str
    phone: str | None
    role: str
    department: str | None
    position: str | None
    avatar: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut
