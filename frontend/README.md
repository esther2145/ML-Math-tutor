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

The tutor and teacher request forms are not connected to FastAPI yet. Sample
exercise feedback is calculated locally and is not saved. Lesson edits remain
in the current page and are not saved. These states are labelled in the UI;
the frontend does not present sample content as live backend output.
