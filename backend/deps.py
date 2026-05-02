from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import SessionLocal
from jose import jwt, JWTError
import models
from auth import SECRET_KEY, ALGORITHM

print("SECRET IN DEPS:", SECRET_KEY)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# extract token manually from header
def get_token(Authorization: str = Header(None)):
    if not Authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    if not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid auth header")

    return Authorization.split(" ")[1]

def get_current_user(token: str = Depends(get_token), db: Session = Depends(get_db)):
    print("TOKEN:", token)

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print("PAYLOAD:", payload)

        user_id = payload.get("user_id")
    except JWTError as e:
        print("JWT ERROR:", str(e))
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    print("USER:", user)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user