from fastapi import APIRouter
from models import User

router = APIRouter()

@router.post("/api/register")
async def register_user(user: User):
    # Logic to add user to the database
    return {"message": "User registered successfully"}