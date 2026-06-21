from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    name: str


class UserRead(BaseModel):
    id: int
    email: str
    name: str

    class Config:
        from_attributes = True
