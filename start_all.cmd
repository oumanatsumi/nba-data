@echo off
setlocal enabledelayedexpansion
set "PROJECT_ROOT=%~dp0"
set "PYTHON=E:\Env\Miniconda\envs\nba-data\python.exe"
set "PORT=8000"
set "PG_DIR=E:\Env\PostgreSQL\17\bin"

echo =============================================
echo   NBA Data API - Start All
echo =============================================
echo.

echo [1/3] PostgreSQL...
2>nul "%PYTHON%" -c "from sqlalchemy import create_engine,text;from dotenv import load_dotenv;import os;load_dotenv(os.path.join(r'%PROJECT_ROOT%','.env'));engine=create_engine(f'postgresql://{os.getenv(\"POSTGRES_USER\",\"postgres\")}:{os.getenv(\"POSTGRES_PASSWORD\",\"postgres\")}@localhost:5432/{os.getenv(\"POSTGRES_DB\",\"nba_data\")}');engine.connect().execute(text('SELECT 1'))" >nul 2>&1 & if !errorlevel! equ 0 (
    echo   [OK] PostgreSQL already running
    goto :pg_done
)

echo   Starting PostgreSQL...
sc query postgresql-x64-17 2>nul | findstr "STOPPED" >nul 2>&1 & net start postgresql-x64-17 >nul 2>&1
sc query postgresql-x64-17 2>nul | findstr "RUNNING" >nul 2>&1 & goto :pg_wait
if exist "%PG_DIR%\pg_ctl.exe" ( "%PG_DIR%\pg_ctl.exe" -D "%PG_DIR%\..\data" start >nul 2>&1 & goto :pg_wait )
echo   [FAIL] Cannot start PostgreSQL
pause & exit /b 1

:pg_wait
for /l %%i in (1,1,30) do (
    2>nul "%PYTHON%" -c "from sqlalchemy import create_engine,text;from dotenv import load_dotenv;import os;load_dotenv(os.path.join(r'%PROJECT_ROOT%','.env'));engine=create_engine(f'postgresql://{os.getenv(\"POSTGRES_USER\",\"postgres\")}:{os.getenv(\"POSTGRES_PASSWORD\",\"postgres\")}@localhost:5432/{os.getenv(\"POSTGRES_DB\",\"nba_data\")}');engine.connect().execute(text('SELECT 1'))" >nul 2>&1 & goto :pg_ready
    timeout /t 1 >nul
)
echo   [FAIL] PostgreSQL timeout
pause & exit /b 1

:pg_ready
echo   [OK] PostgreSQL ready
:pg_done

echo.
echo [2/3] Data check...
for /f %%a in ('2^>^&1 "%PYTHON%" -c "from sqlalchemy import create_engine,text;from dotenv import load_dotenv;import os;load_dotenv(os.path.join(r'%PROJECT_ROOT%','.env'));engine=create_engine(f'postgresql://{os.getenv(\"POSTGRES_USER\",\"postgres\")}:{os.getenv(\"POSTGRES_PASSWORD\",\"postgres\")}@localhost:5432/{os.getenv(\"POSTGRES_DB\",\"nba_data\")}');p=engine.connect().execute(text('SELECT COUNT(*) FROM players')).scalar();g=engine.connect().execute(text('SELECT COUNT(*) FROM games')).scalar();print(f'{p} players, {g} games')"') do echo   [OK] %%a

echo.
echo [3/3] Starting API server...
echo.
echo   =============================================
echo     Server  : http://localhost:%PORT%
echo     Swagger : http://localhost:%PORT%/docs
echo     Health  : http://localhost:%PORT%/health
echo   =============================================
echo     Press Ctrl+C to stop
echo.

cd /d "%PROJECT_ROOT%backend"
"%PYTHON%" -m uvicorn app.main:app --host 0.0.0.0 --port %PORT% --reload