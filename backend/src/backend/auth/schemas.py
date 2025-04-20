from pydantic import BaseModel, Field, ConfigDict

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6)

class UserOut(BaseModel):
    id: int
    username: str = Field(..., max_length=255)

    model_config = ConfigDict(
        from_attributes=True,
    )

class SignupOut(UserOut):
    pass

class LoginOut(Token):
    id: int
    username: str = Field(..., max_length=255)