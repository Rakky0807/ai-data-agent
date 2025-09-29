from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Float
from sqlalchemy.sql import func
from .database import Base
import uuid

class DataSession(Base):
    __tablename__ = "data_sessions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    data_summary = Column(JSON, nullable=True)
    columns_info = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

class QueryHistory(Base):
    __tablename__ = "query_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(JSON, nullable=False)
    created_at = Column(DateTime, server_default=func.now())