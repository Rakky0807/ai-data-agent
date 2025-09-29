import pandas as pd
import numpy as np
import re
from typing import Any, List, Dict
import logging

logger = logging.getLogger(__name__)

class DataCleaner:
    """Clean and standardize uploaded data"""
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Main cleaning pipeline"""
        df = self._handle_unnamed_columns(df)
        df = self._clean_column_names(df)
        df = self._detect_and_convert_types(df)
        df = self._handle_missing_values(df)
        df = self._remove_duplicate_rows(df)
        df = self._standardize_text_columns(df)
        return df
    
    def _handle_unnamed_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle unnamed columns"""
        unnamed_count = 0
        new_columns = []
        
        for col in df.columns:
            if 'Unnamed' in str(col) or pd.isna(col):
                # Check if column has any non-null values
                if df[col].notna().any():
                    # Try to infer column name from first non-null value
                    first_val = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                    if first_val and isinstance(first_val, str) and len(first_val) < 50:
                        new_columns.append(self._clean_column_name(first_val))
                    else:
                        unnamed_count += 1
                        new_columns.append(f"Column_{unnamed_count}")
                else:
                    # Drop entirely empty columns
                    df = df.drop(columns=[col])
            else:
                new_columns.append(str(col))
        
        if len(new_columns) == len(df.columns):
            df.columns = new_columns
        
        return df
    
    def _clean_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize column names"""
        df.columns = [self._clean_column_name(col) for col in df.columns]
        
        # Handle duplicate column names
        cols = pd.Series(df.columns)
        for dup in cols[cols.duplicated()].unique():
            dup_indices = np.where(cols == dup)[0]
            for i, idx in enumerate(dup_indices[1:], 1):
                cols[idx] = f"{dup}_{i}"
        df.columns = cols
        
        return df
    
    def _clean_column_name(self, name: str) -> str:
        """Clean individual column name"""
        name = str(name).strip()
        # Remove special characters but keep underscores
        name = re.sub(r'[^\w\s]', '', name)
        # Replace spaces with underscores
        name = re.sub(r'\s+', '_', name)
        # Remove consecutive underscores
        name = re.sub(r'_+', '_', name)
        # Remove leading/trailing underscores
        name = name.strip('_')
        
        # If name is empty after cleaning, generate one
        if not name:
            name = "Column"
        
        return name
    
    def _detect_and_convert_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect and convert data types intelligently"""
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                try:
                    # Remove common numeric separators
                    cleaned = df[col].astype(str).str.replace(',', '').str.replace('$', '').str.strip()
                    numeric_col = pd.to_numeric(cleaned, errors='coerce')
                    
                    # If more than 50% converted successfully, use numeric
                    if numeric_col.notna().sum() / len(df) > 0.5:
                        df[col] = numeric_col
                        logger.info(f"Converted {col} to numeric")
                        continue
                except:
                    pass
                
                # Try to convert to datetime
                try:
                    # Check if it looks like dates
                    sample = df[col].dropna().head(10).astype(str)
                    if any(char in str(sample.values) for char in ['/', '-', '20', '19']):
                        datetime_col = pd.to_datetime(df[col], errors='coerce')
                        
                        # If more than 50% converted successfully, use datetime
                        if datetime_col.notna().sum() / len(df) > 0.5:
                            df[col] = datetime_col
                            logger.info(f"Converted {col} to datetime")
                            continue
                except:
                    pass
                
                # Try to convert to boolean
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) <= 3:
                    lower_vals = [str(v).lower() for v in unique_vals]
                    if any(val in lower_vals for val in ['true', 'false', 'yes', 'no', '1', '0']):
                        df[col] = df[col].map({
                            'true': True, 'True': True, 'TRUE': True, '1': True, 'yes': True, 'Yes': True, 'YES': True,
                            'false': False, 'False': False, 'FALSE': False, '0': False, 'no': False, 'No': False, 'NO': False
                        })
                        logger.info(f"Converted {col} to boolean")
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values intelligently"""
        for col in df.columns:
            null_count = df[col].isnull().sum()
            
            if null_count == len(df):
                # Drop completely empty columns
                df = df.drop(columns=[col])
                logger.info(f"Dropped empty column: {col}")
            elif null_count > 0:
                null_percentage = null_count / len(df)
                
                if null_percentage > 0.9:
                    # Drop columns with >90% missing values
                    df = df.drop(columns=[col])
                    logger.info(f"Dropped column {col} with {null_percentage:.1%} missing values")
                elif pd.api.types.is_numeric_dtype(df[col]):
                    # For numeric columns with <50% missing, fill with median
                    if null_percentage < 0.5:
                        df[col].fillna(df[col].median(), inplace=True)
                elif pd.api.types.is_string_dtype(df[col]):
                    # For string columns, replace NaN with empty string
                    df[col].fillna('', inplace=True)
        
        # Drop rows that are completely empty
        df = df.dropna(how='all')
        
        return df
    
    def _remove_duplicate_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate rows"""
        original_count = len(df)
        df = df.drop_duplicates()
        removed_count = original_count - len(df)
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate rows")
        
        return df
    
    def _standardize_text_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize text in string columns"""
        for col in df.select_dtypes(include=['object']).columns:
            # Strip whitespace
            df[col] = df[col].astype(str).str.strip()
            
            # Replace multiple spaces with single space
            df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
            
            # Handle common encoding issues
            df[col] = df[col].str.replace('Ã©', 'é').str.replace('Ã', 'à')
            
            # Convert 'nan' string to actual NaN
            df[col] = df[col].replace(['nan', 'NaN', 'NULL', 'null', 'None'], np.nan)
            
        return df
