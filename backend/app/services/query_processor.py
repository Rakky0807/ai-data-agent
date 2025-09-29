# app/services/query_processor.py
import json
import logging
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from ..models import DataSession, QueryHistory
from ..schemas import QueryResponse, ChartSpec
from .llm_service import LLMService

logger = logging.getLogger(__name__)


class QueryProcessor:
    def __init__(self, db: Session):
        self.db = db
        self.llm = LLMService()

    async def process_query(self, session_id: str, query: str) -> QueryResponse:
        """Process natural language query on session data"""
        # Get session
        session = self.db.query(DataSession).filter_by(id=session_id).first()
        if not session:
            return QueryResponse(text="Session not found. Please upload a file first.", sender="ai")

        # Load data
        try:
            df = pd.read_csv(session.file_path)
        except Exception as e:
            logger.error(f"Failed to load processed CSV at {session.file_path}: {e}")
            return QueryResponse(text="Failed to load session data.", sender="ai")

        # Build data context for LLM
        data_context = {
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "shape": df.shape,
            "summary": session.data_summary
        }

        # Get intent from LLM (or fallback)
        intent_analysis = await self.llm.analyze_query(query, data_context)

        # Execute the intent
        result = await self._execute_intent(df, intent_analysis, query)

        # Save to history (store as dict)
        try:
            history = QueryHistory(session_id=session_id, query=query, response=result.dict())
            self.db.add(history)
            self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to save query history: {e}")

        return result

    async def _execute_intent(self, df: pd.DataFrame, intent: Dict, query: str) -> QueryResponse:
        """Route the request to the appropriate handler based on LLM intent"""
        intent_type = intent.get("intent", "summarize")
        columns = intent.get("columns", []) or []
        operation = intent.get("operation", "describe")
        chart_type = intent.get("chart_type")

        try:
            if intent_type == "visualize" or chart_type:
                return await self._create_visualization(df, columns, chart_type, operation)
            elif intent_type == "aggregate":
                return await self._perform_aggregation(df, columns, operation)
            elif intent_type == "filter":
                return await self._filter_data(df, intent.get("filters", {}))
            elif intent_type == "compare":
                return await self._compare_columns(df, columns)
            elif intent_type == "correlation":
                return await self._find_correlations(df)
            else:
                return await self._summarize_data(df, columns)
        except Exception as e:
            logger.error(f"Intent execution error: {e}", exc_info=True)
            return QueryResponse(
                text=f"I encountered an error processing your request: {str(e)}. Could you please rephrase your question?",
                sender="ai"
            )

    # ----------------------
    # Visualization handlers
    # ----------------------
    async def _create_visualization(self, df: pd.DataFrame, columns: List[str],
                                    chart_type: Optional[str] = None, operation: str = "count") -> QueryResponse:
        """Create visualization based on data"""
        # Default to first two columns if none specified
        if not columns:
            columns = df.columns[:2].tolist()

        # Normalize columns to ones present in df
        columns = [c for c in columns if c in df.columns]
        if not columns:
            columns = df.columns[:2].tolist()

        # Single column -> distribution
        if len(columns) == 1:
            col = columns[0]
            if pd.api.types.is_numeric_dtype(df[col]):
                data = df[col].value_counts(bins=10).reset_index()
                data.columns = ["range", "count"]
                chart_data = data.head(20).to_dict("records")
                x_axis = "range"
                y_axis = "count"
            else:
                data = df[col].value_counts().reset_index()
                data.columns = [col, "count"]
                chart_data = data.head(10).to_dict("records")
                x_axis = col
                y_axis = "count"
        else:
            # Two columns or more: take first two
            x_col, y_col = columns[:2]
            # Both numeric -> a simple XY dataset
            if pd.api.types.is_numeric_dtype(df[y_col]):
                if not pd.api.types.is_numeric_dtype(df[x_col]):
                    # group by x_col and aggregate y_col
                    data = df.groupby(x_col)[y_col].agg(operation).reset_index().head(20)
                else:
                    data = df[[x_col, y_col]].dropna().head(200)
            else:
                # categorical combos -> counts
                data = df.groupby([x_col, y_col]).size().reset_index(name="count").head(20)
                y_col = "count"
            chart_data = data.to_dict("records")
            x_axis = x_col
            y_axis = y_col

        # Choose sane chart type only among those supported by frontend: bar, line, pie
        if not chart_type:
            if len(chart_data) <= 5:
                chart_type = "pie"
            elif pd.api.types.is_numeric_dtype(df[columns[0]]) if len(columns) > 0 else False:
                chart_type = "line"
            else:
                chart_type = "bar"

        chart_spec = ChartSpec(
            type=chart_type,
            data=chart_data,
            x_axis=x_axis,
            y_axis=y_axis,
            title=f"{y_axis} by {x_axis}"
        )

        return QueryResponse(
            text=f"Here's a {chart_type} chart showing {y_axis} by {x_axis}. Showing up to {len(chart_data)} items.",
            chart=chart_spec,
            sender="ai"
        )

    # ----------------------
    # Aggregation
    # ----------------------
    async def _perform_aggregation(self, df: pd.DataFrame, columns: List[str], operation: str) -> QueryResponse:
        """Perform aggregation operations on numeric columns"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        if not columns or columns == ["*"]:
            columns = numeric_cols
        else:
            columns = [c for c in columns if c in numeric_cols]

        if not columns:
            return QueryResponse(text="No numeric columns found for aggregation. Please specify numeric columns.", sender="ai")

        if operation == "sum":
            result = df[columns].sum()
        elif operation == "mean":
            result = df[columns].mean()
        elif operation == "count":
            result = df[columns].count()
        elif operation == "max":
            result = df[columns].max()
        elif operation == "min":
            result = df[columns].min()
        else:
            result = df[columns].describe()

        if isinstance(result, pd.Series):
            data = [{"Column": idx, "Value": float(val) if pd.notna(val) else None} for idx, val in result.items()]
        else:
            data = result.reset_index().to_dict("records")

        return QueryResponse(text=f"Here are the {operation} values for the requested columns:", data=data, sender="ai")

    # ----------------------
    # Filtering
    # ----------------------
    async def _filter_data(self, df: pd.DataFrame, filters: Dict[str, Any]) -> QueryResponse:
        """Filter data based on conditions (basic equality-based filters)"""
        filtered_df = df.copy()
        for col, value in (filters or {}).items():
            if col in df.columns:
                filtered_df = filtered_df[filtered_df[col] == value]

        if filtered_df.empty:
            return QueryResponse(text="No data matches the specified filters. Try adjusting your criteria.", sender="ai")

        data = filtered_df.head(20).to_dict("records")
        return QueryResponse(text=f"Found {len(filtered_df)} matching records. Showing the first 20:", data=data, sender="ai")

    # ----------------------
    # Compare columns
    # ----------------------
    async def _compare_columns(self, df: pd.DataFrame, columns: List[str]) -> QueryResponse:
        """Compare multiple columns (statistics + a chart for the first two numeric columns)"""
        if not columns or len(columns) < 2:
            return QueryResponse(text="Please specify at least two columns to compare.", sender="ai")

        columns = [c for c in columns if c in df.columns][:3]  # cap to 3

        comparison_data: List[Dict[str, Any]] = []

        numeric_cols = [c for c in columns if pd.api.types.is_numeric_dtype(df[c])]
        if numeric_cols:
            for col in numeric_cols:
                comparison_data.append({
                    "Column": col,
                    "Mean": float(df[col].mean()),
                    "Median": float(df[col].median()),
                    "Std Dev": float(df[col].std()),
                    "Min": float(df[col].min()),
                    "Max": float(df[col].max())
                })

        cat_cols = [c for c in columns if c not in numeric_cols]
        if cat_cols:
            for col in cat_cols:
                comparison_data.append({
                    "Column": col,
                    "Unique Values": int(df[col].nunique()),
                    "Most Common": str(df[col].mode().iloc[0] if not df[col].mode().empty else "N/A"),
                    "Missing Values": int(df[col].isnull().sum())
                })

        chart = None
        if len(numeric_cols) >= 2:
            # Use a line chart (frontend supports line) with a sample of rows
            sample_df = df[numeric_cols[:2]].dropna().sample(min(100, max(1, len(df))))
            chart_data = sample_df.to_dict("records")
            chart = ChartSpec(
                type="line",  # map scatter -> line so frontend can render it
                data=chart_data,
                x_axis=numeric_cols[0],
                y_axis=numeric_cols[1],
                title=f"Comparison: {numeric_cols[0]} vs {numeric_cols[1]}"
            )

        return QueryResponse(text=f"Comparison of {', '.join(columns)}:", data=comparison_data, chart=chart, sender="ai")

    # ----------------------
    # Correlation
    # ----------------------
    async def _find_correlations(self, df: pd.DataFrame) -> QueryResponse:
        """Find correlations between numeric columns and report the strongest ones"""
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return QueryResponse(text="No numeric columns found for correlation analysis.", sender="ai")

        corr_matrix = numeric_df.corr()
        strong_correlations: List[Dict[str, Any]] = []
        cols = corr_matrix.columns.tolist()
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                corr_value = corr_matrix.iloc[i, j]
                if pd.notna(corr_value) and abs(corr_value) > 0.5:
                    strong_correlations.append({
                        "Column 1": cols[i],
                        "Column 2": cols[j],
                        "Correlation": round(float(corr_value), 3),
                        "Strength": "Strong" if abs(corr_value) > 0.7 else "Moderate"
                    })

        strong_correlations.sort(key=lambda x: abs(x["Correlation"]), reverse=True)
        if not strong_correlations:
            return QueryResponse(text="No strong correlations found between numeric columns (threshold: |r| > 0.5).", sender="ai")

        return QueryResponse(text=f"Found {len(strong_correlations)} significant correlations:", data=strong_correlations[:10], sender="ai")

    # ----------------------
    # Summarize
    # ----------------------
    async def _summarize_data(self, df: pd.DataFrame, columns: List[str]) -> QueryResponse:
        """Provide data summary"""
        if not columns:
            columns = df.columns.tolist()

        columns = [c for c in columns if c in df.columns][:5]  # Limit to 5 columns

        summary_data: List[Dict[str, Any]] = []
        for col in columns:
            col_summary: Dict[str, Any] = {
                "Column": col,
                "Type": str(df[col].dtype),
                "Non-Null Count": int(df[col].count()),
                "Null Count": int(df[col].isnull().sum()),
                "Unique Values": int(df[col].nunique())
            }

            if pd.api.types.is_numeric_dtype(df[col]):
                col_summary.update({
                    "Mean": round(float(df[col].mean()), 2) if df[col].count() > 0 else None,
                    "Min": round(float(df[col].min()), 2) if df[col].count() > 0 else None,
                    "Max": round(float(df[col].max()), 2) if df[col].count() > 0 else None
                })
            else:
                mode_val = df[col].mode()
                col_summary["Most Common"] = str(mode_val.iloc[0]) if not mode_val.empty else "N/A"

            summary_data.append(col_summary)

        # Return a small sample of actual rows too
        sample_data = df[columns].head(10).to_dict("records")
        # To keep UI consistent, return the sample rows (frontend shows data tables).
        # Full column-summary is available in `summary_data` if you want to surface it later.
        return QueryResponse(text=f"Summary of {', '.join(columns)}:", data=sample_data, sender="ai")
