from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

import models
from database import engine
from deps import get_db
from auth import hash_password, verify_password, create_token

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Root route (so "/" works)
@app.get("/")
def root():
    return {"message": "API is running"}


# Signup
@app.post("/signup")
def signup(email: str, password: str, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == email).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    new_user = models.User(
        email=email,
        password=hash_password(password)  # ✅ FIXED
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created"}


# Login
@app.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user or not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    token = create_token({"user_id": user.id})

    return {"access_token": token}