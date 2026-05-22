import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_admin = Column(Boolean, default=False)
    
    predictions = relationship("Prediction", back_populates="user")

class Match(Base):
    __tablename__ = 'matches'
    id = Column(Integer, primary_key=True)
    group = Column(String(10), nullable=False)
    team_a = Column(String(50), nullable=False)
    flag_a = Column(String(10), nullable=True)
    team_b = Column(String(50), nullable=False)
    flag_b = Column(String(10), nullable=True)
    date = Column(DateTime, nullable=False)
    time = Column(String(10), nullable=True)
    stadium = Column(String(100), nullable=True)
    status = Column(String(20), default='pending') # pending, finished
    result_a = Column(Integer, nullable=True)
    result_b = Column(Integer, nullable=True)
    
    predictions = relationship("Prediction", back_populates="match")

class Prediction(Base):
    __tablename__ = 'predictions'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    pred_a = Column(Integer, nullable=False)
    pred_b = Column(Integer, nullable=False)
    points = Column(Integer, default=0)
    
    user = relationship("User", back_populates="predictions")
    match = relationship("Match", back_populates="predictions")

class SystemConfig(Base):
    __tablename__ = 'system_config'
    key = Column(String(50), primary_key=True)
    value = Column(String(200), nullable=False)

# Setup Database
try:
    import streamlit as st
    DB_PATH = st.secrets["DATABASE_URL"]
except Exception:
    DB_PATH = os.environ.get("DATABASE_URL", "sqlite:///prode_v2.db")
engine = create_engine(DB_PATH)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
