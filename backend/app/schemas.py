from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class FileUploadResponse(BaseModel):
    session_id: str
    message: str
    data_summary: Optional[Dict[str, Any]] = None

class QueryRequest(BaseModel):
    session_id: str
    query: str

class ChartSpec(BaseModel):
    type: str  # 'bar', 'line', 'pie'
    data: List[Dict[str, Any]]
    x_axis: str
    y_axis: str
    title: Optional[str] = None

class QueryResponse(BaseModel):
    sender: str = "ai"
    text: str
    data: Optional[List[Dict[str, Any]]] = None
    chart: Optional[ChartSpec] = None