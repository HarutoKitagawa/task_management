from fastapi import APIRouter, Depends

from ..auth.dependencies import get_current_user
from ..models import User
from .schemas import UserOut

router = APIRouter()

@router.get("/users/me", response_model=UserOut)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return UserOut(id=current_user.id, username=current_user.username)