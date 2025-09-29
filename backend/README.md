# AI Data Agent Backend - Complete Setup Guide

## Prerequisites

- **Python 3.9+** (Check: `python --version`)
- **MySQL 8.0+** (Check: `mysql --version`)
- **Ollama** (Free local LLM)

---

## Step 1: Install Ollama

### Windows
1. Download from: https://ollama.com/download/windows
2. Run the installer
3. Verify: Open CMD and type `ollama --version`

### macOS
```bash
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

---

## Step 2: Download LLM Model

```bash
# Start Ollama service (in a terminal - keep it running)
ollama serve

# In ANOTHER terminal, download the model
ollama pull llama3.2:3b

# Verify it downloaded
ollama list
```

**Note:** Keep the `ollama serve` terminal running while using the app.

---

## Step 3: Setup MySQL Database

### Start MySQL Server
```bash
# Windows (via MySQL Installer or XAMPP)
# macOS
brew services start mysql
# Linux
sudo systemctl start mysql
```

### Create Database and User
```sql
-- Login to MySQL
mysql -u root -p

-- Create database
CREATE DATABASE ai_data_agent;

-- Create user (change password!)
CREATE USER 'aiagent'@'localhost' IDENTIFIED BY 'SecurePassword123!';

-- Grant permissions
GRANT ALL PRIVILEGES ON ai_data_agent.* TO 'aiagent'@'localhost';
FLUSH PRIVILEGES;

-- Exit
EXIT;
```

---

## Step 4: Backend Setup

### Navigate to Backend Directory
```bash
cd backend
```

### Create Virtual Environment
```bash
# Create venv
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Configure Environment Variables
```bash
# Copy example file
cp .env.example .env

# Edit .env file with your settings
# Use: notepad .env (Windows) or nano .env (Mac/Linux)
```

**Update these values in .env:**
```env
DATABASE_URL=mysql+pymysql://aiagent:SecurePassword123!@localhost/ai_data_agent
SECRET_KEY=change-this-to-random-secret-key-in-production
OLLAMA_HOST=http://localhost:11434
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=10485760
```

---

## Step 5: Initialize Database Tables

```bash
# The tables will be created automatically when you run the app
# But you can test database connection:
python -c "from app.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine); print('Database tables created successfully!')"
```

---

## Step 6: Run the Backend

```bash
# Make sure you're in backend directory with venv activated
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Test Backend
Open browser: http://localhost:8000

You should see:
```json
{
  "message": "AI Data Agent API is running",
  "version": "1.0.0",
  "endpoints": ["/upload", "/query", "/health"]
}
```

---

## Step 7: Run Frontend

```bash
# In a NEW terminal, navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

Open browser: http://localhost:5173

---

## Troubleshooting

### Issue: "Module not found" errors
```bash
pip install --upgrade -r requirements.txt
```

### Issue: MySQL connection failed
- Verify MySQL is running: `sudo systemctl status mysql` (Linux) or check Services (Windows)
- Check credentials in `.env` file
- Test connection: `mysql -u aiagent -p ai_data_agent`

### Issue: Ollama not responding
```bash
# Stop and restart Ollama
pkill ollama
ollama serve
```

### Issue: "Port 8000 already in use"
```bash
# Find and kill process
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:8000 | xargs kill -9
```

### Issue: CORS errors in frontend
- Check that backend is running on port 8000
- Verify CORS_ORIGINS in `app/config.py` includes your frontend URL

---

## File Upload Testing

### Test Files
Create a sample Excel file with:
- Multiple columns (mix of text and numbers)
- Some missing values
- At least 20 rows

### Sample Queries to Test
1. "Show me a summary of the data"
2. "Create a bar chart of [column_name]"
3. "What's the average of [numeric_column]?"
4. "Show me the top 5 [category]"
5. "Find correlations between numeric columns"

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py        # API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_service.py      # File upload handling
│   │   ├── data_analyzer.py     # Data analysis
│   │   ├── llm_service.py       # Ollama LLM integration
│   │   └── query_processor.py   # Query processing logic
│   └── utils/
│       ├── __init__.py
│       ├── data_cleaner.py      # Data cleaning utilities
│       └── chart_generator.py   # Chart specification generation
├── uploads/                 # Uploaded files (auto-created)
├── requirements.txt
├── .env.example
├── .env                     # Your config (create this)
├── setup.py
└── README.md
```

---

## Development Tips

### Running in Production
```bash
# Don't use --reload in production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Viewing Logs
```bash
# Backend logs appear in terminal
# Check uploads directory: ls -la uploads/
```

### Database Management
```bash
# View tables
mysql -u aiagent -p ai_data_agent -e "SHOW TABLES;"

# View sessions
mysql -u aiagent -p ai_data_agent -e "SELECT * FROM data_sessions;"

# Clear all data (careful!)
mysql -u aiagent -p ai_data_agent -e "TRUNCATE TABLE query_history; TRUNCATE TABLE data_sessions;"
```

---

## API Endpoints

### POST /upload
Upload Excel/CSV file
```bash
curl -X POST http://localhost:8000/upload \
  -F "file=@/path/to/your/file.xlsx"
```

### POST /query
Query uploaded data
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"session_id": "your-session-id", "query": "Show me the data"}'
```

### GET /health
Health check
```bash
curl http://localhost:8000/health
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Slow LLM responses | Use llama3.2:3b (smaller, faster) |
| Out of memory | Reduce MAX_FILE_SIZE in .env |
| Charts not showing | Check browser console for errors |
| File upload fails | Check UPLOAD_DIR permissions |

---

## Next Steps

1. Test with various Excel files (clean and dirty data)
2. Try different query types
3. Monitor backend logs for errors
4. Adjust LLM prompts in `llm_service.py` if needed

---

## Support

For issues, check:
1. Backend terminal for error messages
2. Frontend browser console (F12)
3. MySQL logs: `sudo tail -f /var/log/mysql/error.log`
4. Ollama logs: Check terminal running `ollama serve`

---

## Built for SDE Hiring Assignment