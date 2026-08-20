# G-RAFT Math Tutor

G-RAFT is a primary mathematics tutor API that combines a Neo4j curriculum
graph, Qdrant learning-material retrieval, and a local Ollama language model.

## Quick start with Docker

1. Copy `.env.example` to `.env` and replace the Neo4j password.
2. Start the services:

   ```powershell
   docker compose up --build -d
   ```

3. Download the configured Ollama model once:

   ```powershell
   docker compose exec ollama ollama pull llama3.2:3b
   ```

4. Load the starter curriculum and learning materials:

   ```powershell
   Invoke-RestMethod -Method Post http://localhost:8000/load-curriculum
   Invoke-RestMethod -Method Post http://localhost:8000/vector/load-materials
   ```

5. Open `http://localhost:8000/docs` and try `POST /tutor/ask`.

The CSV files in `data/` are small starter datasets intended for development,
not a complete or officially validated national curriculum.

## Local development

Create and activate a Python 3.11+ virtual environment, then install the app and
development tools:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn backend.main:app --reload
```

Neo4j, Qdrant, and Ollama must be running, and the variables documented in
`.env.example` must point to them.

Run checks with:

```powershell
python -m compileall -q backend
pytest
ruff check backend tests
```
