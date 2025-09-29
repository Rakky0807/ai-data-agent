# backend/app/config.py

import os
from pathlib import Path
from dotenv import load_dotenv

# 🎯 FIX: Load the .env file at the very top
load_dotenv()

class Settings:
    # Database
    # This will now correctly read from your .env file
    DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:password@localhost/ai_data_agent")
    
    # Ollama LLM
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    
    # File Upload
    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 10 * 1024 * 1024))  # 10MB
    ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}
    
    # Session
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
    
    # CORS
    CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
    
    def __init__(self):
        # This ensures the upload directory exists when the app starts
        self.UPLOAD_DIR.mkdir(exist_ok=True)

settings = Settings()