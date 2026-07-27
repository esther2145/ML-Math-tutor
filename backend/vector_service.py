import os
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "math_learning_materials"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# all-MiniLM-L6-v2 generates vectors with 384 dimensions.
VECTOR_SIZE = 384

client = QdrantClient(url=QDRANT_URL)

# The embedding model is loaded once when the application starts.
embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)


def test_qdrant_connection() -> dict[str, Any]:
    """Check whether Qdrant is reachable."""

    try:
        collections = client.get_collections()

        return {
            "connected": True,
            "collections": [
                collection.name
                for collection in collections.collections
            ],
        }

    except Exception as error:
        return {
            "connected": False,
            "error": str(error),
        }


def create_collection() -> str:
    """Create the Qdrant collection if it does not exist."""

    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )

        return f"Collection '{COLLECTION_NAME}' created successfully."

    return f"Collection '{COLLECTION_NAME}' already exists."


def load_materials(
    csv_path: str = "../data/learning_materials.csv",
) -> int:
    """Convert learning materials into embeddings and store them."""

    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Learning-material file was not found: {path.resolve()}"
        )

    create_collection()

    dataframe = pd.read_csv(path)

    required_columns = {
        "id",
        "topic",
        "grade",
        "title",
        "content",
    }

    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        raise ValueError(
            f"Missing CSV columns: {sorted(missing_columns)}"
        )

    texts = dataframe["content"].fillna("").astype(str).tolist()

    vectors = embedding_model.encode(
        texts,
        normalize_embeddings=True,
    )

    points = []

    for row, vector in zip(
        dataframe.to_dict(orient="records"),
        vectors,
    ):
        points.append(
            models.PointStruct(
                id=int(row["id"]),
                vector=vector.tolist(),
                payload={
                    "topic": str(row["topic"]),
                    "grade": int(row["grade"]),
                    "title": str(row["title"]),
                    "content": str(row["content"]),
                },
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
        wait=True,
    )

    return len(points)


def search_materials(
    question: str,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Retrieve learning materials that are semantically related."""

    question_vector = embedding_model.encode(
        question,
        normalize_embeddings=True,
    ).tolist()

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=question_vector,
        limit=limit,
        with_payload=True,
    ).points

    return [
        {
            "score": round(float(result.score), 4),
            "topic": result.payload.get("topic"),
            "grade": result.payload.get("grade"),
            "title": result.payload.get("title"),
            "content": result.payload.get("content"),
        }
        for result in results
    ]