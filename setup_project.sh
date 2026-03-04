#!/bin/bash
# ============================================================
#   Medical LightRAG API — Project Setup (Linux/macOS/Git Bash)
#   Run this file once to set up everything from scratch.
#   Usage: chmod +x setup_project.sh && ./setup_project.sh
# ============================================================

set -e  # Exit on any error

echo ""
echo "============================================================"
echo "  Medical LightRAG API — Automatic Setup"
echo "============================================================"
echo ""

# --------------------------------------------------
# 1. Check Python
# --------------------------------------------------
echo "[1/7] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "   ERROR: Python is not installed!"
        echo "   Please install Python 3.11+ first."
        echo "   Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
        echo "   macOS: brew install python"
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi
echo "   Found: $($PYTHON_CMD --version)"
echo ""

# --------------------------------------------------
# 2. Create virtual environment
# --------------------------------------------------
echo "[2/7] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   Virtual environment already exists. Skipping..."
else
    $PYTHON_CMD -m venv venv
    echo "   Virtual environment created successfully!"
fi
echo ""

# --------------------------------------------------
# 3. Activate venv and install dependencies
# --------------------------------------------------
echo "[3/7] Installing dependencies from requirements.txt..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

pip install --upgrade pip --quiet
pip install -r requirements.txt
echo "   All dependencies installed successfully!"
echo ""

# --------------------------------------------------
# 4. Create required directories
# --------------------------------------------------
echo "[4/7] Creating project directories..."

mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/contextualized
mkdir -p lightrag_data
mkdir -p logs

echo "   Created: data/raw/              (place your raw PDF/JSON files here)"
echo "   Created: data/processed/        (processed JSON files ready for ingestion)"
echo "   Created: data/contextualized/   (AI-enhanced JSON after contextualization)"
echo "   Created: lightrag_data/         (LightRAG Knowledge Graph storage)"
echo "   Created: logs/                  (application logs)"
echo ""

# --------------------------------------------------
# 5. Set up environment file
# --------------------------------------------------
echo "[5/7] Setting up environment configuration..."
if [ -f ".env" ]; then
    echo "   .env file already exists. Skipping..."
    echo "   NOTE: If you need a fresh config, delete .env and run this script again."
else
    if [ -f ".env.local" ]; then
        cp .env.local .env
        echo "   Copied .env.local to .env"
    else
        echo "   WARNING: No .env.local template found!"
        echo "   Please create a .env file manually with your configuration."
        echo "   At minimum, you need: GEMINI_API_KEY, DATABASE_URL"
    fi
fi
echo ""

# --------------------------------------------------
# 6. Remind about PostgreSQL
# --------------------------------------------------
echo "[6/7] Database setup reminder..."
echo ""
echo "   This project requires PostgreSQL. You have two options:"
echo ""
echo "   Option A — Docker (recommended):"
echo "     docker-compose up -d postgres"
echo ""
echo "   Option B — Local PostgreSQL:"
echo "     1. Install PostgreSQL 15+"
echo "     2. Create database: chatbot_rhm"
echo "     3. Update DATABASE_URL in .env"
echo ""

# --------------------------------------------------
# 7. Verify setup
# --------------------------------------------------
echo "[7/7] Verifying installation..."
echo ""

$PYTHON_CMD -c "import fastapi; print('    FastAPI............. OK (v' + fastapi.__version__ + ')')" 2>/dev/null || echo "    FastAPI............. FAILED"
$PYTHON_CMD -c "import pocketflow; print('    PocketFlow......... OK')" 2>/dev/null || echo "    PocketFlow......... FAILED"
$PYTHON_CMD -c "import google.genai; print('    Google GenAI........ OK')" 2>/dev/null || echo "    Google GenAI........ FAILED"
$PYTHON_CMD -c "import lightrag; print('    LightRAG........... OK')" 2>/dev/null || echo "    LightRAG........... FAILED"
$PYTHON_CMD -c "import rank_bm25; print('    rank-bm25.......... OK')" 2>/dev/null || echo "    rank-bm25.......... FAILED"
$PYTHON_CMD -c "import sqlalchemy; print('    SQLAlchemy......... OK')" 2>/dev/null || echo "    SQLAlchemy......... FAILED"
$PYTHON_CMD -c "from core.nodes.SafetyGuardrailNode import SafetyGuardrailNode; print('    SafetyGuardrailNode OK')" 2>/dev/null || echo "    SafetyGuardrailNode FAILED"
$PYTHON_CMD -c "from core.flows.advanced_medical_flow import AdvancedMedicalFlow; print('    AdvancedMedicalFlow OK')" 2>/dev/null || echo "    AdvancedMedicalFlow FAILED"

echo ""
echo "============================================================"
echo "  SETUP COMPLETE!"
echo "============================================================"
echo ""
echo "  Next steps:"
echo ""
echo "  1. Edit .env and set your GEMINI_API_KEY"
echo "     nano .env"
echo ""
echo "  2. Start PostgreSQL (if not running)"
echo "     docker-compose up -d postgres"
echo ""
echo "  3. Prepare your data (place JSON files in data/processed/)"
echo '     JSON format: {"source": "...", "page": 1, "content": "..."}'
echo ""
echo "  4. (Optional) Contextualize data for better AI accuracy"
echo "     python scripts/contextualize_json.py --input-dir data/processed/ --output-dir data/contextualized/"
echo ""
echo "  5. Ingest data into LightRAG"
echo "     python scripts/ingest_json_to_lightrag.py"
echo ""
echo "  6. Start the API server"
echo "     python start_api.py"
echo ""
echo "  7. Open API docs in browser"
echo "     http://localhost:8000/api/docs"
echo ""
echo "============================================================"
