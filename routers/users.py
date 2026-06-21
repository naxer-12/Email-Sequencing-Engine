from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas import UserCreate, UserRead
from services import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead, status_code=201)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    print(f"Creating user with email: {user.email} and name: {user.name}")
    print(f"Database session: {db}")
    print(f"UserCreate object: {user}")
    return user_service.create_user(db, user)


@router.get("/{user_id}", response_model=UserRead)
async def read_user(user_id: int, db: Session = Depends(get_db)):
    return user_service.get_user(db, user_id)


@router.get("/", response_model=list[UserRead])
async def list_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    return user_service.list_users(db, skip, limit)


@router.put("/{user_id}", response_model=UserRead)
async def update_user(user_id: int, email: str, db: Session = Depends(get_db)):
    return user_service.update_user(db, user_id, email)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user_service.delete_user(db, user_id)
