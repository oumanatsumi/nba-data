@echo off
REM =============================================
REM  NBA Data API ? One-click launcher
REM =============================================

setlocal

set PROJECT_ROOT=%~dp0
set CONDA_ENV=E:\Env\Miniconda\envs\nba-data
set PYTHON=%CONDA_ENV%\python.exe
set PORT=8000

echo =============================================
echo   NBA Data API Launcher
echo =============================================
echo.

REM Step 1: Check PostgreSQL
echo [1/3] Checking PostgreSQL...
%PYTHON% -c "from sqlalchemy import create_engine; from dotenv import load_dotenv; import os; load_dotenv(os.path.join(r'%PROJECT_ROOT%', '.env')); engine = create_engine(f'postgresql://{os.getenv(\"POSTGRES_USER\",\"postgres\")}:{os.getenv(\"POSTGRES_PASSWORD\",\"postgres\")}@localhost:5432/{os.getenv(\"POSTGRES_DB\",\"nba_data\")}'); conn = engine.connect(); conn.close()" 2>&1 | findstr "Connected" >nul 2>&1
if %errorlevel% neq 0 (
    echo   [FAIL] Cannot connect to PostgreSQL
    echo   Run: net start postgresql-x64-17
    pause
    exit /b 1
)
echo   [OK] PostgreSQL connected

REM Step 2: Check data
echo [2/3] Checking data...
%PYTHON% -c "from sqlalchemy import create_engine, text; from dotenv import load_dotenv; import os; load_dotenv(os.path.join(r'%PROJECT_ROOT%', '.env')); engine = create_engine(f'postgresql://{os.getenv(\"POSTGRES_USER\",\"postgres\")}:{os.getenv(\"POSTGRES_PASSWORD\",\"postgres\")}@localhost:5432/{os.getenv(\"POSTGRES_DB\",\"nba_data\")}'); c = engine.connect().execute(text('SELECT COUNT(*) FROM players')).scalar(); print(f'{c} players', f'{engine.connect().execute(text(\"SELECT COUNT(*) FROM games\")).scalar()} games')" 2>&1 | findstr "players"
echo   [OK] Data ready

REM Step 3: Start server
echo [3/3] Starting API server...
echo.
echo   =============================================
echo     Server:  http://localhost:%PORT%
echo     Docs:    http://localhost:%PORT%/docs
echo     Health:  http://localhost:%PORT%/health
echo   =============================================
echo.

cd /d "%PROJECT_ROOT%backend"
%PYTHON% -m uvicorn app.main:app --host 0.0.0.0 --port %PORT% --reload
