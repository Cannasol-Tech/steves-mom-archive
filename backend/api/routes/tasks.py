import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ...database import get_db
from ...functions.approval.approval_handler import ApprovalHandler
from ...models import orm, task_models
from ...models.orm.approval_history import ApprovalHistory
from ..connection_manager import manager

router = APIRouter()


@router.post("/tasks/", response_model=task_models.Task, status_code=201)
def create_task(task: task_models.Task, db: Session = Depends(get_db)):
    db_task = orm.task.Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@router.get("/tasks/{task_id}", response_model=task_models.Task)
def read_task(task_id: uuid.UUID, db: Session = Depends(get_db)):
    db_task = db.query(orm.task.Task).filter(orm.task.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@router.get("/tasks/", response_model=List[task_models.Task])
def read_tasks(
    status: Optional[task_models.TaskStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(orm.task.Task)
    if status:
        query = query.filter(orm.task.Task.status == status)
    if start_date:
        query = query.filter(orm.task.Task.created_at >= start_date)
    if end_date:
        query = query.filter(orm.task.Task.created_at <= end_date)
    if search:
        query = query.filter(
            or_(
                orm.task.Task.title.ilike(f"%{search}%"),
                orm.task.Task.description.ilike(f"%{search}%"),
            )
        )
    tasks = query.offset(skip).limit(limit).all()
    return tasks


@router.put("/tasks/{task_id}", response_model=task_models.Task)
async def update_task(
    task_id: uuid.UUID, task: task_models.TaskUpdate, db: Session = Depends(get_db)
):
    db_task = db.query(orm.task.Task).filter(orm.task.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    for key, value in task.model_dump(exclude_unset=True).items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)
    # Broadcast the update to all connected clients
    await manager.broadcast(task_models.Task.model_validate(db_task).model_dump_json())
    return db_task


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: uuid.UUID, db: Session = Depends(get_db)):
    db_task = db.query(orm.task.Task).filter(orm.task.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(db_task)
    db.commit()
    return


@router.post("/tasks/{task_id}/approve", response_model=task_models.Task)
async def approve_task(task_id: uuid.UUID, db: Session = Depends(get_db)):
    db_task = db.query(orm.task.Task).filter(orm.task.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    history_entry = ApprovalHistory(
        task_id=db_task.id, status=task_models.TaskStatus.APPROVED
    )
    db.add(history_entry)

    approval_handler = ApprovalHandler(db_task)
    try:
        approval_handler.approve()
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    db.commit()
    db.refresh(db_task)
    await manager.broadcast(task_models.Task.model_validate(db_task).model_dump_json())
    return db_task


@router.post("/tasks/{task_id}/reject", response_model=task_models.Task)
async def reject_task(task_id: uuid.UUID, db: Session = Depends(get_db)):
    db_task = db.query(orm.task.Task).filter(orm.task.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    history_entry = ApprovalHistory(
        task_id=db_task.id, status=task_models.TaskStatus.REJECTED
    )
    db.add(history_entry)

    approval_handler = ApprovalHandler(db_task)
    try:
        approval_handler.reject()
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    db.commit()
    db.refresh(db_task)
    await manager.broadcast(task_models.Task.model_validate(db_task).model_dump_json())
    return db_task


@router.get("/tasks/analytics")
def get_task_analytics(db: Session = Depends(get_db)):
    """Get task analytics including counts by status."""
    # Count tasks by status
    total_tasks = db.query(orm.task.Task).count()
    accepted = db.query(orm.task.Task).filter(orm.task.Task.status == task_models.TaskStatus.APPROVED).count()
    rejected = db.query(orm.task.Task).filter(orm.task.Task.status == task_models.TaskStatus.REJECTED).count()
    modified = db.query(orm.task.Task).filter(orm.task.Task.status == task_models.TaskStatus.IN_PROGRESS).count()

    return {
        "totalTasks": total_tasks,
        "accepted": accepted,
        "rejected": rejected,
        "modified": modified
    }
