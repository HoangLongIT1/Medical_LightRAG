@echo off
chcp 65001 >nul
REM ============================================================
REM   Medical LightRAG API — Project Setup (Windows CMD/PowerShell)
REM   Run this file once to set up everything from scratch.
REM ============================================================

echo.
echo ============================================================
echo   Medical LightRAG API — Automatic Setup
echo ============================================================
echo.

REM --------------------------------------------------
REM 1. Check Python
REM --------------------------------------------------
echo [1/7] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo    ERROR: Python is not installed or not in PATH!
    echo    Please install Python 3.11+ from https://www.python.org/downloads/
    echo    Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do echo    Found Python %%v
echo.

REM --------------------------------------------------
REM 2. Create virtual environment
REM --------------------------------------------------
echo [2/7] Creating virtual environment...
if exist "venv" (
    echo    Virtual environment already exists. Skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo    ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo    Virtual environment created successfully!
)
echo.

REM --------------------------------------------------
REM 3. Activate venv and install dependencies
REM --------------------------------------------------
echo [3/7] Installing dependencies from requirements.txt...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt
if errorlevel 1 (
    echo    ERROR: Failed to install some dependencies!
    echo    Check the error messages above and try again.
    pause
    exit /b 1
)
echo    All dependencies installed successfully!
echo.

REM --------------------------------------------------
REM 4. Create required directories
REM --------------------------------------------------
echo [4/7] Creating project directories...

if not exist "data" mkdir data
if not exist "data\raw" mkdir data\raw
if not exist "data\processed" mkdir data\processed
if not exist "data\contextualized" mkdir data\contextualized
if not exist "lightrag_data" mkdir lightrag_data
if not exist "logs" mkdir logs

echo    Created: data\raw\              (place your raw PDF/JSON files here)
echo    Created: data\processed\        (processed JSON files ready for ingestion)
echo    Created: data\contextualized\   (AI-enhanced JSON after contextualization)
echo    Created: lightrag_data\         (LightRAG Knowledge Graph storage)
echo    Created: logs\                  (application logs)
echo.

REM --------------------------------------------------
REM 5. Set up environment file
REM --------------------------------------------------
echo [5/7] Setting up environment configuration...
if exist ".env" (
    echo    .env file already exists. Skipping...
    echo    NOTE: If you need a fresh config, delete .env and run this script again.
) else (
    if exist ".env.local" (
        copy .env.local .env >nul
        echo    Copied .env.local to .env
    ) else (
        echo    WARNING: No .env.local template found!
        echo    Please create a .env file manually with your configuration.
        echo    At minimum, you need: GEMINI_API_KEY, DATABASE_URL
    )
)
echo.

REM --------------------------------------------------
REM 6. Remind about PostgreSQL
REM --------------------------------------------------
echo [6/7] Database setup reminder...
echo.
echo    This project requires PostgreSQL. You have two options:
echo.
echo    Option A — Docker (recommended):
echo      docker-compose up -d postgres
echo.
echo    Option B — Local PostgreSQL:
echo      1. Install PostgreSQL 15+
echo      2. Create database: chatbot_rhm
echo      3. Update DATABASE_URL in .env
echo.

REM --------------------------------------------------
REM 7. Verify setup
REM --------------------------------------------------
echo [7/7] Verifying installation...
echo.

python -c "import fastapi; print('    FastAPI............. OK (v' + fastapi.__version__ + ')')"
python -c "import pocketflow; print('    PocketFlow......... OK')"
python -c "import google.genai; print('    Google GenAI........ OK')"
python -c "import lightrag; print('    LightRAG........... OK')"
python -c "import rank_bm25; print('    rank-bm25.......... OK')"
python -c "import sqlalchemy; print('    SQLAlchemy......... OK')"
python -c "from core.nodes.SafetyGuardrailNode import SafetyGuardrailNode; print('    SafetyGuardrailNode OK')"
python -c "from core.flows.advanced_medical_flow import AdvancedMedicalFlow; print('    AdvancedMedicalFlow OK')"

echo.
echo ============================================================
echo   SETUP COMPLETE!
echo ============================================================
echo.
echo   Next steps:
echo.
echo   1. Edit .env and set your GEMINI_API_KEY
echo      notepad .env
echo.
echo   2. Start PostgreSQL (if not running)
echo      docker-compose up -d postgres
echo.
echo   3. Prepare your data (place JSON files in data\processed\)
echo      JSON format: {"source": "...", "page": 1, "content": "..."}
echo.
echo   4. (Optional) Contextualize data for better AI accuracy
echo      python scripts\contextualize_json.py --input-dir data\processed\ --output-dir data\contextualized\
echo.
echo   5. Ingest data into LightRAG
echo      python scripts\ingest_json_to_lightrag.py
echo.
echo   6. Start the API server
echo      python start_api.py
echo.
echo   7. Open API docs in browser
echo      http://localhost:8000/api/docs
echo.
echo ============================================================
pause
