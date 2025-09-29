from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import FileUploadResponse, QueryRequest, QueryResponse
from ..services.file_service import FileService
from ..services.query_processor import QueryProcessor
from ..config import settings
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process Excel/CSV file"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        file_ext = '.' + file.filename.split('.')[-1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type not supported. Allowed: {settings.ALLOWED_EXTENSIONS}"
            )
        
        # Process file
        file_service = FileService(db)
        result = await file_service.process_upload(file)
        
        return result
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """Process natural language query on uploaded data"""
    try:
        processor = QueryProcessor(db)
        response = await processor.process_query(
            session_id=request.session_id,
            query=request.query
        )
        return response
        
    except Exception as e:
        logger.error(f"Query processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))