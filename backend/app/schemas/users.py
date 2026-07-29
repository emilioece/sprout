from datetime import datetime
from pydantic import BaseModel, EmailStr

# Request model used when registering a new account
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# Response model returned by API (never includes the password)
class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        from_attributes = True