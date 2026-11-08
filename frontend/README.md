# G-RAFT frontend

This is a separate React, TypeScript, and Vite application. It does not replace
the Streamlit interface or access Neo4j, Qdrant, or Ollama directly.

## Run on Windows

From the repository root, install the JavaScript dependencies once:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite. In another terminal, the existing FastAPI
and Streamlit applications can still be started using the commands in the
repository's main README.

## Current prototype scope

All five proposed frontend routes are available:

- `/` — choose learner or teacher space
- `/learn` — learner tutor interface preview
- `/learn/practice` — one local sample exercise
- `/teacher` — teaching-assistant request form preview
- `/teacher/lesson` — editable lesson outline template with print support

The learner tutor at `/learn` calls the existing `POST /tutor/ask` endpoint
through Vite's `/api` development proxy. Start FastAPI at
`http://127.0.0.1:8000` in a separate terminal. The selected grade, answer,
verification status, and retrieval details are displayed. Conversation history
is only shown in the browser; prior messages are not sent as context to the
backend.

The teacher request form and lesson generation are not connected to FastAPI.
Sample practice feedback is calculated locally and is not saved. Lesson edits
remain in the current page and are not saved. These states are labelled in the
UI; sample content is not presented as live backend output.
