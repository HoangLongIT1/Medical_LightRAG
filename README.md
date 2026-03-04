# Medical LightRAG — Multi-Agent Medical API

Medical chatbot API powered by **Hybrid Search** (BM25 + Vector + Knowledge Graph) with a multi-agent architecture built on **PocketFlow**.

## Architecture

```
Layer 1 (Cognitive):  IngestQuery → ClinicalStateManager
Layer 2 (Routing):    MasterMedicalRouter
Layer 3 (Execution):  8 Specialist Agents → Hybrid Search (BM25 + Graph + Vector)
Layer 4 (Output):     ComposeAnswer (+ Safety Disclaimer)
Layer 5 (Memory):     MemoryManager → Add/Update/Delete
```

### Specialist Agents (8 chuyên khoa)

| Agent | Route | Specialty |
|-------|-------|-----------|
| InternalMedicineAgent | `noi_khoa` | Nội Khoa — cardiovascular, respiratory, GI, endocrine |
| PediatricsAgent | `nhi_khoa` | Nhi Khoa — child diseases, dosing, vaccines |
| PharmacologyAgent | `duoc_ly` | Dược Lý — drug interactions, dosing, contraindications |
| SurgeryAgent | `ngoai_khoa` | Ngoại Khoa — trauma, fractures, burns, perioperative care |
| OdontologyAgent | `nha_khoa` | Nha Khoa — dental caries, periodontics, orthodontics, implants |
| ObstetricsAgent | `san_khoa` | Sản Khoa — pregnancy, labor/delivery, postpartum, gynecology |
| DermatologyAgent | `da_lieu` | Đa Liễu — skin infections, eczema, psoriasis, acne, allergies |
| PsychiatryAgent | `tam_than` | Tâm Thần — depression, anxiety, sleep, stress (crisis hotline: 1800 599 100) |

### Safety Layer

Responses involving medication (dosage, drug names, contraindications) or sensitive specialists (Dược Lý, Tâm Thần, Sản Khoa) automatically include a disclaimer:

> ⚠️ **Lưu ý:** Thông tin do AI cung cấp có thể chưa hoàn toàn chính xác. Vui lòng tham khảo thêm ý kiến của chuyên gia trong lĩnh vực liên quan trước khi áp dụng bất kỳ phương pháp điều trị nào.

## Tech Stack

- **Backend**: FastAPI + Uvicorn
- **RAG Engine**: LightRAG (Graph + Vector retrieval via `lightrag-hku`)
- **Hybrid Search**: BM25 keyword matching (`rank-bm25`) + Graph + Vector
- **LLM**: Google Gemini (`google-genai`)
- **Embedding**: `gemini-embedding-001`
- **Agent Framework**: PocketFlow
- **Database**: PostgreSQL (chat history, clinical states, user auth)
- **Tracing**: Langfuse (optional)

## Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (for containerized deployment)

## Quick Start

### Run Locally

```bash
# 1. Copy environment config
copy .env.local .env

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start PostgreSQL (if not running)
docker-compose up -d postgres

# 4. Start API server
python start_api.py
```

### Run with Docker

```bash
# Copy docker environment config
copy .env.docker .env

# Build and start all services
docker-compose up --build -d
```

### Load Data into LightRAG

```bash
# Optional: Add context headers for better retrieval accuracy
python scripts/contextualize_json.py --input-dir data/processed/ --output-dir data/contextualized/

# Ingest JSON data into LightRAG (auto-builds BM25 index)
python scripts/ingest_json_to_lightrag.py

# Verify Hybrid Search is working
python scripts/verify_hybrid_search.py
```

Or use the API:

1. Open API docs: `http://localhost:8000/api/docs`
2. Use `POST /api/lightrag/documents/text` to insert medical documents
3. Use `POST /api/lightrag/documents/batch` for bulk insertion

## API Endpoints

| Category | Endpoint | Description |
|----------|----------|-------------|
| **Chat** | `POST /api/chat` | Main conversation endpoint |
| **LightRAG** | `POST /api/lightrag/query` | Query with search modes |
| **LightRAG** | `POST /api/lightrag/query/context` | Context-only retrieval |
| **LightRAG** | `POST /api/lightrag/documents/text` | Insert documents |
| **LightRAG** | `POST /api/lightrag/documents/batch` | Batch insert |
| **Auth** | `POST /api/auth/login` | User login |
| **Health** | `GET /api/health` | Health check |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `DATABASE_URL` | PostgreSQL connection string |
| `LIGHTRAG_WORKING_DIR` | Directory for LightRAG data |
| `LIGHTRAG_LLM_MODEL` | LLM model for LightRAG |

See `.env.local` for full list.

## Project Structure

```
├── api/                    # FastAPI route handlers
│   ├── chat.py             # Main chat endpoint
│   ├── lightrag_docs.py    # LightRAG document management
│   └── lightrag_query.py   # LightRAG query endpoints
├── core/
│   ├── nodes/              # PocketFlow node implementations
│   │   ├── ClinicalStateManager.py   # Symptom tracking (Layer 1)
│   │   ├── MasterMedicalRouter.py    # Intent routing (Layer 2)
│   │   ├── SpecialistAgents.py       # 8 specialist agents (Layer 3)
│   │   ├── RetrieveFromKBWithDemuc.py # Hybrid Search retrieval
│   │   └── ComposeAnswer.py          # Response generation + safety disclaimer
│   └── flows/
│       ├── medical_flow.py           # Basic medical flow
│       └── advanced_medical_flow.py  # Full 5-layer pipeline (9 routes)
├── config/                 # Configuration modules
├── database/               # SQLAlchemy models & DB setup
├── scripts/
│   ├── ingest_json_to_lightrag.py   # JSON data ingestion
│   ├── contextualize_json.py        # Contextual Retrieval preprocessor
│   └── verify_hybrid_search.py      # Hybrid Search verification
├── utils/
│   ├── lightrag_engine.py  # LightRAG singleton + BM25Index
│   └── llm/                # LLM utilities & prompts
└── start_api.py            # Application entry point
```
