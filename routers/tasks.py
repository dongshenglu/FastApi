from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from starlette import status

from database import SessionLocal
from models import Tasks
from routers.auth import get_current_user

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class TaskRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(ge=0, lt=6)
    complete: bool

    class Config:
        json_schema_extra = {
            'example': {
                'title': 'A new task',
                'description': 'A new description of a task',
                'priority': 2,
                'complete': False
            }
        }


def validate_user(user: user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed.')


def find_task(user: user_dependency, db: db_dependency, task_id: int = Path(gt=0)):
    task_model = (db.query(Tasks).filter(Tasks.id == task_id)
                  .filter(int(Tasks.owner_id) == user.get('id')).first())
    if task_model is not None:
        return task_model
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found.')


@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    validate_user(user)
    return db.query(Tasks).filter(int(Tasks.owner_id) == user.get('id')).all()


@router.get("/tasks/{task_id}", status_code=status.HTTP_200_OK)
async def read_task(user: user_dependency, db: db_dependency, task_id: int = Path(gt=0)):
    validate_user(user)
    find_task(user, db, task_id)


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(user: user_dependency, db: db_dependency, task_request: TaskRequest):
    validate_user(user)

    task_model = Tasks(**task_request.model_dump(), owner_id=user.get('id'))
    db.add(task_model)
    db.commit()


@router.put("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_task(user: user_dependency, db: db_dependency,
                      task_request: TaskRequest,
                      task_id: int = Path(gt=0)):
    validate_user(user)

    task_model = find_task(user, db, task_id)
    task_model.title = task_request.title
    task_model.description = task_request.description
    task_model.priority = task_request.priority
    task_model.complete = task_request.complete

    db.add(task_model)
    db.commit()


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(user: user_dependency, db: db_dependency, task_id: int = Path(gt=0)):
    validate_user(user)

    find_task(user, db, task_id)
    db.query(Tasks).filter(Tasks.id == task_id).filter(int(Tasks.owner_id) == user.get('id')).delete()
    db.commit()
