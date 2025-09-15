from fastapi import APIRouter, Depends
from db.models import User
from security.auth import get_current_user

router = APIRouter()

@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username}

@router.get("/protected-data")
async def get_protected_data(current_user: User = Depends(get_current_user)):
    return {"message": "This is some top secret protected data!"}