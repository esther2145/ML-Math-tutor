from fastapi import FastAPI, HTTPException
from database import test_connection, create_basic_math_graph
from graph_loader import load_curriculum_to_graph
from graph_service import get_topic_details
from pydantic import BaseModel
from ollama_service import test_ollama_connection, generate_response

app = FastAPI(
    title="G-RAFT Math Tutor API",
    version="1.0"
    
)
class PromptRequest(BaseModel):
        prompt: str

@app.get("/")
def home():
    return {"message": "Backend is running"}


@app.get("/test-db")
def database_test():
    message = test_connection()
    return {"database": message}

@app.post("/create-basic-graph")
def create_graph():
    message = create_basic_math_graph()
    return {"message": message}

@app.post("/load-curriculum")
def load_curriculum():
    message = load_curriculum_to_graph()
    return {"message": message}

@app.get("/topic/{topic_name}")
def topic_details(topic_name: str):
    topic = get_topic_details(topic_name)

    if topic is None:
        return {"error": "Topic not found"}

    return topic

@app.get("/test-ollama")
def test_ollama():
    result = test_ollama_connection()

    if not result["connected"]:
        raise HTTPException(
            status_code=503,
            detail=result["error"],
        )

    return result


@app.post("/generate")
def generate(request: PromptRequest):
    if not request.prompt.strip():
        raise HTTPException(
            status_code=400,
            detail="The prompt cannot be empty.",
        )

    try:
        answer = generate_response(request.prompt)

        return {
            "prompt": request.prompt,
            "answer": answer,
        }

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        )
