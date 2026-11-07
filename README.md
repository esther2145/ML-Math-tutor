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

   To load the richer concepts, examples, grades, and relationships instead,
   use the idempotent advanced loader:

   ```powershell
   Invoke-RestMethod -Method Post http://localhost:8000/graph/load-complete
   ```

5. Open the learner interface at `http://localhost:8501`.

The API documentation remains available at `http://localhost:8000/docs`.

The CSV files in `data/` are small starter datasets intended for development,
not a complete or officially validated national curriculum.
The [data sourcing guide](data/README.md) explains the country-specific intake
templates, source tracking, and review requirements.
It also describes the initial evaluation set and how its arithmetic, policy,
and blocked curriculum cases should be interpreted separately.

## React frontend prototype

The separate React and TypeScript interface lives in `frontend/`; it does not
replace Streamlit. To run it on Windows, install Node.js, then in a PowerShell
terminal run:

```powershell
cd frontend
npm install
npm run dev
```

The frontend currently provides navigable learner and teacher interface
previews. Chat and teacher requests are not connected to FastAPI yet. See
`frontend/README.md` for the current prototype scope.

## Local development

Create and activate a Python 3.11+ virtual environment, then install the app and
development tools:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,ui]"
uvicorn backend.main:app --reload
```

In another terminal, start the learner interface:

```powershell
streamlit run streamlit_app.py
```

Neo4j, Qdrant, and Ollama must be running, and the variables documented in
`.env.example` must point to them.

When FastAPI runs on the host while Qdrant runs through Compose, keep
`QDRANT_PORT` and the port in `QDRANT_URL` aligned. Both default to `6333`.

Run checks with:

```powershell
python -m compileall -q backend
pytest
ruff check .
```

## Docker troubleshooting on Windows

If Docker reports access denied for the named pipe or `.docker/config.json`,
start Docker Desktop under the same Windows account as the terminal. Confirm
Docker is ready with `docker version` before running Compose. If access to the
configuration file is still denied, correct that file's permissions through
Windows Properties > Security, then restart Docker Desktop.
