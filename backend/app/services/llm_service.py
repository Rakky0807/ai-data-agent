import ollama
import json
import logging
from typing import Dict, Any, Optional
import re

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, model_name: str = "llama3.2:3b"):
        self.model_name = model_name
        self.client = ollama.Client()
        
    async def analyze_query(self, query: str, data_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user query and determine intent"""
        
        prompt = f"""You are a data analysis assistant. Analyze this query and determine what the user wants.

Data Context:
- Columns: {data_context.get('columns', [])}
- Data types: {data_context.get('dtypes', {})}
- Row count: {data_context.get('shape', [0])[0]}

User Query: "{query}"

Respond in JSON format with:
{{
    "intent": "one of: summarize, filter, aggregate, visualize, compare, correlation",
    "columns": ["list of relevant columns"],
    "operation": "specific operation like sum, mean, count, etc",
    "filters": {{"column": "value"}},
    "chart_type": "if visualization: bar, line, pie, scatter",
    "explanation": "brief explanation of what you understood"
}}
"""
        
        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                format="json",
                stream=False
            )
            
            # Parse response
            result = json.loads(response['response'])
            return result
            
        except Exception as e:
            logger.error(f"LLM analysis error: {str(e)}")
            # Fallback to regex-based analysis
            return self._fallback_analysis(query, data_context)
    
    def _fallback_analysis(self, query: str, data_context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback query analysis using regex patterns"""
        query_lower = query.lower()
        columns = data_context.get('columns', [])
        
        # Detect intent
        intent = "summarize"
        if any(word in query_lower for word in ['chart', 'plot', 'graph', 'visualize']):
            intent = "visualize"
        elif any(word in query_lower for word in ['filter', 'where', 'only']):
            intent = "filter"
        elif any(word in query_lower for word in ['average', 'sum', 'total', 'count', 'mean']):
            intent = "aggregate"
        elif any(word in query_lower for word in ['compare', 'versus', 'vs']):
            intent = "compare"
        elif any(word in query_lower for word in ['correlation', 'relate']):
            intent = "correlation"
        
        # Detect columns mentioned
        mentioned_cols = []
        for col in columns:
            if col.lower() in query_lower:
                mentioned_cols.append(col)
        
        # Detect chart type
        chart_type = None
        if 'bar' in query_lower:
            chart_type = 'bar'
        elif 'line' in query_lower:
            chart_type = 'line'
        elif 'pie' in query_lower:
            chart_type = 'pie'
        
        return {
            "intent": intent,
            "columns": mentioned_cols or columns[:2],
            "operation": self._detect_operation(query_lower),
            "filters": {},
            "chart_type": chart_type,
            "explanation": f"I understood you want to {intent} the data"
        }
    
    def _detect_operation(self, query: str) -> str:
        """Detect mathematical operation from query"""
        if 'sum' in query or 'total' in query:
            return 'sum'
        elif 'average' in query or 'mean' in query:
            return 'mean'
        elif 'count' in query:
            return 'count'
        elif 'max' in query or 'maximum' in query:
            return 'max'
        elif 'min' in query or 'minimum' in query:
            return 'min'
        return 'describe'
    
    async def generate_sql_query(self, intent_analysis: Dict, table_name: str = "data") -> str:
        """Generate SQL query based on intent analysis"""
        intent = intent_analysis.get('intent', 'summarize')
        columns = intent_analysis.get('columns', ['*'])
        operation = intent_analysis.get('operation', 'select')
        filters = intent_analysis.get('filters', {})
        
        # Build SQL query
        if intent == 'summarize':
            return f"SELECT * FROM {table_name} LIMIT 10"
        
        elif intent == 'aggregate':
            if operation in ['sum', 'mean', 'count', 'max', 'min']:
                agg_cols = ', '.join([f"{operation.upper()}({col}) as {col}_{operation}" 
                                     for col in columns if col != '*'])
                return f"SELECT {agg_cols} FROM {table_name}"
        
        elif intent == 'filter':
            where_clause = ' AND '.join([f"{k} = '{v}'" for k, v in filters.items()])
            return f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT 100"
        
        return f"SELECT * FROM {table_name} LIMIT 10"