from pydantic import BaseModel, Field, ConfigDict

class UserOut(BaseModel):
    id: int
    username: str = Field(..., max_length=255)

    model_config = ConfigDict(
        from_attributes=True,
    )