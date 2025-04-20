from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..database import get_db
from ..models import User
from .schemas import UserOut

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[UserOut])
async def list_users(
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    users = db.query(User).all()
    if keyword:
        users = [user for user in users if keyword in user.username]
    return [UserOut.model_validate(user) for user in users]