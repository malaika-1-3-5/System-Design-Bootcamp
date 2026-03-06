import uuid
from fastapi import FastAPI, APIRouter, status, HTTPException, Depends
from sqlalchemy import create_engine, Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from contextlib import contextmanager

engine = create_engine("postgresql://agriadmin:agriadmin123@localhost:5632/agri_db")
SessionLocal = sessionmaker[Session](autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI() #Creating an instance of FastAPI
app_v1 = APIRouter(prefix="/api/v1", tags=["v1"])

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

users = ["user1", "user2", "user4"]

#class User():
    #def __init__(self, id: int, name: str, email: str, password: str):
        #self.id = id
        #self.name = name
        #self.email = email
        #self.password = password

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)



def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app_v1.get("/users/{id}", status_code=status.HTTP_200_OK)
def getuserbyId(id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: str

    #response = UserResponse(id=user.id, name=user.name, email=user.email)
    #return response

@app_v1.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    user = User(name=user.name, email=user.email, password=user.password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created successfully"}

#in terminal: uvicorn rest:app --port 8888
             #uvicorn rest:app --port 8888 --reload

app.include_router(app_v1) #Only at the end