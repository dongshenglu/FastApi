from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from starlette import status

from database import SessionLocal
from models import Tasks
from routers.auth import get_current_user

router = APIRouter(
    prefix='/admin',
    tags=['admin']
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


def validate_admin(user: user_dependency):
    if user is None or user.get('user_role') != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication Failed.')


@router.get("/tasks", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependency, db: db_dependency):
    validate_admin(user)
    return db.query(Tasks).all()


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, task_id: int = Path(gt=0)):
    validate_admin(user)

    task_model = db.query(Tasks).filter(Tasks.id == task_id).first()
    if task_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found.')

    db.query(Tasks).filter(Tasks.id == task_id).delete()
    db.commit()
