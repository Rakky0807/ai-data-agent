import pandas as pd
import numpy as np
from pathlib import Path
import uuid
import aiofiles
from fastapi import UploadFile
from sqlalchemy.orm import Session
from ..models import DataSession
from ..config import settings
from ..utils.data_cleaner import DataCleaner
from .data_analyzer import DataAnalyzer
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def make_dict_json_serializable(d):
    """
    Recursively converts a dictionary to be JSON serializable.
    Handles pandas Timestamps, numpy generic types, and NaN/Inf values.
    """
    if isinstance(d, dict):
        return {k: make_dict_json_serializable(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [make_dict_json_serializable(i) for i in d]
    elif isinstance(d, (pd.Timestamp, datetime)):
        return d.isoformat()
    elif isinstance(d, np.generic):
        return d.item()
    elif isinstance(d, float) and not np.isfinite(d):
        return None  # Convert NaN/Inf to null for JSON compatibility
    else:
        return d

class FileService:
    def __init__(self, db: Session):
        self.db = db
        
    async def process_upload(self, file: UploadFile) -> dict:
        """Process uploaded file and store metadata"""
        session_id = str(uuid.uuid4())
        file_path = settings.UPLOAD_DIR / f"{session_id}_{file.filename}"
        
        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Load and analyze data
        df = self._load_file(file_path)
        
        # Clean data
        cleaner = DataCleaner()
        df = cleaner.clean_dataframe(df)
        
        # Analyze data
        analyzer = DataAnalyzer()
        summary = analyzer.analyze_dataframe(df)
        columns_info = self._get_columns_info(df)
        
        # Ensure summary and columns_info are JSON serializable before DB insertion
        serializable_summary = make_dict_json_serializable(summary)
        serializable_columns_info = make_dict_json_serializable(columns_info)
        
        # Store processed data as CSV for easier access
        processed_path = settings.UPLOAD_DIR / f"{session_id}_processed.csv"
        df.to_csv(processed_path, index=False)
        
        # Save session to database
        session = DataSession(
            id=session_id,
            file_name=file.filename,
            file_path=str(processed_path),
            data_summary=serializable_summary,
            columns_info=serializable_columns_info
        )
        self.db.add(session)
        self.db.commit()
        
        # Generate initial message
        initial_message = self._generate_initial_message(df, summary)
        
        return {
            "session_id": session_id,
            "message": initial_message,
            "data_summary": serializable_summary
        }
    
    def _load_file(self, file_path: Path) -> pd.DataFrame:
        """Load Excel or CSV file"""
        if file_path.suffix.lower() == '.csv':
            return pd.read_csv(file_path)
        else:
            # Try to read Excel with multiple sheets
            excel_file = pd.ExcelFile(file_path)
            if len(excel_file.sheet_names) > 1:
                # Combine all sheets
                dfs = []
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    df['_sheet_name'] = sheet_name
                    dfs.append(df)
                return pd.concat(dfs, ignore_index=True)
            else:
                return pd.read_excel(file_path)
    
    def _get_columns_info(self, df: pd.DataFrame) -> dict:
        """Get detailed column information"""
        info = {}
        for col in df.columns:
            info[col] = {
                "dtype": str(df[col].dtype),
                "unique_values": int(df[col].nunique()),
                "null_count": int(df[col].isnull().sum()),
                "sample_values": df[col].dropna().head(3).tolist()
            }
        return info
    
    def _generate_initial_message(self, df: pd.DataFrame, summary: dict) -> str:
        """Generate welcoming message with data overview"""
        return f"""✨ I've successfully loaded your data!
Here's what I found:

📊 **Data Overview:**
- {len(df)} rows × {len(df.columns)} columns
- Columns: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}

💡 **Quick Insights:**
- Numeric columns: {len([c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])])}
- Text columns: {len([c for c in df.columns if pd.api.types.is_string_dtype(df[c])])}
- Missing values: {'Yes, in some columns' if df.isnull().any().any() else 'No missing values'}

Feel free to ask me anything about your data!
For example:
- "Show me the distribution of [column name]"
- "What are the top 5 [category]?"
- "Create a chart comparing [column1] vs [column2]"
- "Find correlations between numeric columns"
"""