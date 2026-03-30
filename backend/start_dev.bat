@echo off
REM Development server startup script

REM Set environment variables
set DB_TYPE=sqlite
set SQLITE_DB_PATH=fund_selection.db
set SKIP_INIT=true
set USE_REAL_FACTORS=true
set LOG_LEVEL=INFO

REM Start backend server
echo Starting FastAPI backend on http://localhost:8000
echo Database: SQLite (fund_selection.db)
echo Real Factors: ENABLED
echo.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --log-level info
