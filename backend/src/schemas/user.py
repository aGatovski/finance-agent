from pydantic import BaseModel, EmailStr

class User(BaseModel):
    email: str
    password: str
    full_name: str

