from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import datetime

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Models
class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    risk_score = Column(Float)
    assessment_date = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(String)

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    title = Column(String)
    content = Column(String)
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

# Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pydantic models
class UserProfileCreate(BaseModel):
    username: str
    email: str

class RiskAssessmentCreate(BaseModel):
    user_id: int
    risk_score: float
    details: str

class ReportCreate(BaseModel):
    user_id: int
    title: str
    content: str

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/risks", response_model=List[RiskAssessmentCreate])
async def get_risks(db: Session = Depends(get_db)):
    risks = db.query(RiskAssessment).all()
    return risks

@app.post("/api/risks/evaluate", response_model=RiskAssessmentCreate)
async def evaluate_risk(risk: RiskAssessmentCreate, db: Session = Depends(get_db)):
    db_risk = RiskAssessment(**risk.dict())
    db.add(db_risk)
    db.commit()
    db.refresh(db_risk)
    return db_risk

@app.get("/api/user/{user_id}", response_model=UserProfileCreate)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/api/user/{user_id}", response_model=UserProfileCreate)
async def update_user(user_id: int, user: UserProfileCreate, db: Session = Depends(get_db)):
    db_user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.username = user.username
    db_user.email = user.email
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/api/reports", response_model=List[ReportCreate])
async def get_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).all()
    return reports

# Seed data
@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    if not db.query(UserProfile).first():
        db.add(UserProfile(username="admin", email="admin@example.com"))
        db.add(RiskAssessment(user_id=1, risk_score=75.5, details="Initial risk assessment"))
        db.add(Report(user_id=1, title="Initial Report", content="This is a sample report."))
        db.commit()
    db.close()
