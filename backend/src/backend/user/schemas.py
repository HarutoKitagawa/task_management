from pydantic import BaseModel, Field

class UserOut(BaseModel):
    id: int
    username: str = Field(..., max_length=255)