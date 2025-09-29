import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ChartGenerator:
    """Generate chart specifications for frontend visualization"""
    
    @staticmethod
    def create_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, 
                        agg_func: str = 'mean', limit: int = 20) -> Dict[str, Any]:
        """Create bar chart specification"""
        try:
            if pd.api.types.is_numeric_dtype(df[y_col]):
                # Aggregate if x is categorical
                if not pd.api.types.is_numeric_dtype(df[x_col]):
                    data = df.groupby(x_col)[y_col].agg(agg_func).reset_index()
                    data = data.nlargest(limit, y_col)
                else:
                    # If both numeric, bin the x values
                    df['x_binned'] = pd.cut(df[x_col], bins=min(limit, 10))
                    data = df.groupby('x_binned')[y_col].agg(agg_func).reset_index()
                    data.columns = [x_col, y_col]
            else:
                # Count occurrences
                data = df.groupby([x_col, y_col]).size().reset_index(name='count')
                data = data.nlargest(limit, 'count')
                y_col = 'count'
            
            return {
                'type': 'bar',
                'data': data.to_dict('records'),
                'x_axis': x_col,
                'y_axis': y_col,
                'title': f'{y_col} by {x_col}'
            }
        except Exception as e:
            logger.error(f"Bar chart generation error: {str(e)}")
            return None
    
    @staticmethod
    def create_line_chart(df: pd.DataFrame, x_col: str, y_col: str, 
                         limit: int = 50) -> Dict[str, Any]:
        """Create line chart specification"""
        try:
            # Ensure x column is sorted
            data = df[[x_col, y_col]].dropna().sort_values(x_col)
            
            # If too many points, sample them
            if len(data) > limit:
                # Take evenly spaced points
                indices = np.linspace(0, len(data) - 1, limit, dtype=int)
                data = data.iloc[indices]
            
            return {
                'type': 'line',
                'data': data.to_dict('records'),
                'x_axis': x_col,
                'y_axis': y_col,
                'title': f'{y_col} over {x_col}'
            }
        except Exception as e:
            logger.error(f"Line chart generation error: {str(e)}")
            return None
    
    @staticmethod
    def create_pie_chart(df: pd.DataFrame, category_col: str, 
                        value_col: str = None, limit: int = 8) -> Dict[str, Any]:
        """Create pie chart specification"""
        try:
            if value_col and pd.api.types.is_numeric_dtype(df[value_col]):
                # Sum values by category
                data = df.groupby(category_col)[value_col].sum().reset_index()
                data = data.nlargest(limit, value_col)
            else:
                # Count occurrences
                data = df[category_col].value_counts().head(limit).reset_index()
                data.columns = [category_col, 'count']
                value_col = 'count'
            
            # Add percentage
            total = data[value_col].sum()
            data['percentage'] = (data[value_col] / total * 100).round(1)
            
            return {
                'type': 'pie',
                'data': data.to_dict('records'),
                'x_axis': category_col,
                'y_axis': value_col,
                'title': f'Distribution of {category_col}'
            }
        except Exception as e:
            logger.error(f"Pie chart generation error: {str(e)}")
            return None
    
    @staticmethod
    def create_scatter_plot(df: pd.DataFrame, x_col: str, y_col: str, 
                          limit: int = 100) -> Dict[str, Any]:
        """Create scatter plot specification"""
        try:
            # Sample if too many points
            data = df[[x_col, y_col]].dropna()
            if len(data) > limit:
                data = data.sample(n=limit, random_state=42)
            
            return {
                'type': 'scatter',
                'data': data.to_dict('records'),
                'x_axis': x_col,
                'y_axis': y_col,
                'title': f'{y_col} vs {x_col}'
            }
        except Exception as e:
            logger.error(f"Scatter plot generation error: {str(e)}")
            return None
    
    @staticmethod
    def auto_select_chart(df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
        """Automatically select best chart type based on data"""
        if not columns:
            return None
        
        if len(columns) == 1:
            col = columns[0]
            if pd.api.types.is_numeric_dtype(df[col]):
                # Create histogram
                bins = pd.cut(df[col], bins=10)
                data = bins.value_counts().reset_index()
                data.columns = ['range', 'count']
                return {
                    'type': 'bar',
                    'data': data.to_dict('records'),
                    'x_axis': 'range',
                    'y_axis': 'count',
                    'title': f'Distribution of {col}'
                }
            else:
                # Create value counts
                return ChartGenerator.create_pie_chart(df, col)
        
        elif len(columns) == 2:
            x_col, y_col = columns[:2]
            x_is_numeric = pd.api.types.is_numeric_dtype(df[x_col])
            y_is_numeric = pd.api.types.is_numeric_dtype(df[y_col])
            
            if x_is_numeric and y_is_numeric:
                # Both numeric - scatter or line
                if df[x_col].nunique() > 20:
                    return ChartGenerator.create_scatter_plot(df, x_col, y_col)
                else:
                    return ChartGenerator.create_line_chart(df, x_col, y_col)
            elif not x_is_numeric and y_is_numeric:
                # Categorical x, numeric y - bar chart
                return ChartGenerator.create_bar_chart(df, x_col, y_col)
            elif x_is_numeric and not y_is_numeric:
                # Numeric x, categorical y - switch them
                return ChartGenerator.create_bar_chart(df, y_col, x_col)
            else:
                # Both categorical - count combinations
                data = df.groupby([x_col, y_col]).size().reset_index(name='count')
                data = data.nlargest(20, 'count')
                return {
                    'type': 'bar',
                    'data': data.to_dict('records'),
                    'x_axis': x_col,
                    'y_axis': 'count',
                    'title': f'{x_col} and {y_col} combinations'
                }
        
        return None
