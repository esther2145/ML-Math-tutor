from fastapi import FastAPI, HTTPException
from database import test_connection, create_basic_math_graph
from graph_loader import load_curriculum_to_graph
from graph_service import get_topic_details
from pydantic import BaseModel
from ollama_service import test_ollama_connection, generate_response
from tutor_service import explain_topic
from vector_service import (
    load_materials,
    search_materials,
    test_qdrant_connection,
)
from hybrid_tutor_service import answer_math_question


app = FastAPI(
    title="G-RAFT Math Tutor API",
    version="1.0"
    
)
class PromptRequest(BaseModel):
        prompt: str

class TutorRequest(BaseModel):
    topic: str
    learner_grade: int | None = None

class SearchRequest(BaseModel):
    question: str
    limit: int = 3

class TutorQuestionRequest(BaseModel):
    question: str
    learner_grade: int | None = None
    result_limit: int = 3



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

@app.post("/tutor/explain")
def tutor_explanation(request: TutorRequest):
    if not request.topic.strip():
        raise HTTPException(
            status_code=400,
            detail="The topic cannot be empty.",
        )

    if request.learner_grade is not None:
        if request.learner_grade < 1 or request.learner_grade > 7:
            raise HTTPException(
                status_code=400,
                detail="Learner grade must be between 1 and 7.",
            )

    try:
        result = explain_topic(
            topic_name=request.topic,
            learner_grade=request.learner_grade,
        )

        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"Topic '{request.topic}' was not found in the curriculum graph.",
            )

        return result

    except HTTPException:
        raise

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        )
@app.get("/test-qdrant")
def test_qdrant():
    result = test_qdrant_connection()

    if not result["connected"]:
        raise HTTPException(
            status_code=503,
            detail=result["error"],
        )

    return result


@app.post("/vector/load-materials")
def vector_load_materials():
    try:
        number_loaded = load_materials()

        return {
            "message": "Learning materials loaded successfully.",
            "number_loaded": number_loaded,
        }

    except (FileNotFoundError, ValueError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=f"Could not load materials into Qdrant: {error}",
        )


@app.post("/vector/search")
def vector_search(request: SearchRequest):
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="The question cannot be empty.",
        )

    if request.limit < 1 or request.limit > 10:
        raise HTTPException(
            status_code=400,
            detail="The result limit must be between 1 and 10.",
        )

    try:
        results = search_materials(
            question=request.question,
            limit=request.limit,
        )

        return {
            "question": request.question,
            "number_of_results": len(results),
            "results": results,
        }

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=f"Vector search failed: {error}",
        )

@app.post("/tutor/ask")
def ask_tutor(request: TutorQuestionRequest):
    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="The question cannot be empty.",
        )

    if request.learner_grade is not None:
        if request.learner_grade < 1 or request.learner_grade > 7:
            raise HTTPException(
                status_code=400,
                detail="Learner grade must be between 1 and 7.",
            )

    if request.result_limit < 1 or request.result_limit > 5:
        raise HTTPException(
            status_code=400,
            detail="The result limit must be between 1 and 5.",
        )

    try:
        result = answer_math_question(
            question=request.question,
            learner_grade=request.learner_grade,
            result_limit=request.result_limit,
        )

        return result

    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"The tutor could not answer the question: {error}",
        )




