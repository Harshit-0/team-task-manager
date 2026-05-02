from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

import models
from database import engine
from deps import get_db, get_current_user, require_admin
from auth import hash_password, verify_password, create_token
from schemas import UserCreate, UserLogin, ProjectCreate, TaskCreate, TaskUpdate

# Create tables (important for Railway)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def root():
    return {"message": "API is running"}


# ---------------- AUTH ----------------

@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = models.User(
        email=user.email,
        password=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created"}


@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_token({"user_id": db_user.id})

    return {"access_token": token}


@app.get("/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }

# ---------------- PROJECT ----------------

@app.post("/projects")
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin)
):
    new_project = models.Project(
        name=project.name,
        created_by=admin.id
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


# ---------------- TASK ----------------

@app.post("/tasks")
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user = db.query(models.User).filter(models.User.id == task.assigned_to).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_task = models.Task(
        title=task.title,
        assigned_to=task.assigned_to,
        project_id=task.project_id,
        due_date=task.due_date
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task


@app.patch("/tasks/{task_id}")
def update_task(
    task_id: int,
    update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if update.status not in ["todo", "in_progress", "done"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    task.status = update.status
    db.commit()

    return task


@app.get("/tasks/me")
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Task).filter(models.Task.assigned_to == current_user.id).all()


@app.get("/tasks/overdue")
def get_overdue_tasks(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    now = datetime.utcnow()

    return db.query(models.Task).filter(
        models.Task.assigned_to == current_user.id,
        models.Task.due_date != None,
        models.Task.due_date < now,
        models.Task.status != "done"
    ).all()