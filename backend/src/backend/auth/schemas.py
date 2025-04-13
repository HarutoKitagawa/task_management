from pydantic import BaseModel, Field

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6)

class SignupOut(BaseModel):
    id: int
    username: str