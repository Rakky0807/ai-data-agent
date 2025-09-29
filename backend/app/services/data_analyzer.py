import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging
logger = logging.getLogger(__name__)

class DataAnalyzer:
    def analyze_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive dataframe analysis"""
        try:
            summary = {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.astype(str).to_dict(),
                "missing_values": df.isnull().sum().to_dict(),
                "statistics": {},
                "patterns": {}
            }
            
            # Numeric statistics
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                summary["statistics"]["numeric"] = df[numeric_cols].describe().to_dict()
            
            # Categorical statistics
            categorical_cols = df.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0:
                cat_stats = {}
                for col in categorical_cols[:10]:  # Limit to first 10
                    value_counts = df[col].value_counts().head(10)
                    cat_stats[col] = {
                        "unique_count": df[col].nunique(),
                        "top_values": value_counts.to_dict()
                    }
                summary["statistics"]["categorical"] = cat_stats
            
            # Detect patterns
            summary["patterns"] = self._detect_patterns(df)
            
            return summary
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            return {"error": str(e)}
    
    def _detect_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect data patterns and anomalies"""
        patterns = {}
        
        # Date columns
        date_cols = []
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    pd.to_datetime(df[col].dropna().head(100))
                    date_cols.append(col)
                except:
                    pass
        patterns["potential_date_columns"] = date_cols
        
        # ID columns (high cardinality)
        patterns["potential_id_columns"] = [
            col for col in df.columns
            if df[col].nunique() / len(df) > 0.95
        ]
        
        # Constant columns
        patterns["constant_columns"] = [
            col for col in df.columns
            if df[col].nunique() == 1
        ]
        
        return patterns