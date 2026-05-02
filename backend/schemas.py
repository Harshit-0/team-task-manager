from pydantic import BaseModel
from datetime import datetime


class UserCreate(BaseModel):
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class ProjectCreate(BaseModel):
    name: str


class TaskCreate(BaseModel):
    title: str
    assigned_to: int
    project_id: int
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    status: str