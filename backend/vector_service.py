import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import pandas as pd
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from sentence_transformers import SentenceTransformer

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_TIMEOUT = float(os.getenv("QDRANT_TIMEOUT", "60"))
COLLECTION_NAME = "math_learning_materials"
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MINIMUM_RELEVANCE_SCORE = float(os.getenv("MINIMUM_RELEVANCE_SCORE", "0.35"))
DEFAULT_MATERIALS_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "learning_materials.csv"
)

# all-MiniLM-L6-v2 generates vectors with 384 dimensions.
VECTOR_SIZE = 384

client = QdrantClient(url=QDRANT_URL, timeout=QDRANT_TIMEOUT)


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load the embedding model only when vector work is requested."""

    return SentenceTransformer(EMBEDDING_MODEL_NAME)


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
    csv_path: str | Path = DEFAULT_MATERIALS_PATH,
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

    texts = [
        f"{row.topic}. {row.title}. {row.content}"
        for row in dataframe[["topic", "title", "content"]]
        .fillna("")
        .itertuples(index=False)
    ]

    vectors = get_embedding_model().encode(
        texts,
        normalize_embeddings=True,
    )

    points = []

    for row, vector in zip(
        dataframe.to_dict(orient="records"),
        vectors,
        strict=True,
    ):
        country_code = clean_optional_value(row.get("country_code"))
        source_status = (
            clean_optional_value(row.get("source_status"))
            or "prototype_unverified"
        )
        points.append(
            models.PointStruct(
                id=int(row["id"]),
                vector=vector.tolist(),
                payload={
                    "topic": str(row["topic"]),
                    "grade": int(row["grade"]),
                    "title": str(row["title"]),
                    "content": str(row["content"]),
                    "country_code": (
                        country_code.upper()
                        if country_code
                        else None
                    ),
                    "curriculum_name": clean_optional_value(
                        row.get("curriculum_name")
                    ),
                    "curriculum_version": clean_optional_value(
                        row.get("curriculum_version")
                    ),
                    "source_title": clean_optional_value(
                        row.get("source_title")
                    ),
                    "source_url": clean_optional_value(
                        row.get("source_url")
                    ),
                    "source_page": clean_optional_value(
                        row.get("source_page")
                    ),
                    "source_license": clean_optional_value(
                        row.get("source_license")
                    ),
                    "source_status": source_status,
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
    learner_grade: int | None = None,
    country_code: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve learning materials that are semantically related."""

    question_vector = get_embedding_model().encode(
        question,
        normalize_embeddings=True,
    ).tolist()

    filter_conditions = []

    if learner_grade is not None:
        filter_conditions.append(
            models.FieldCondition(
                key="grade",
                range=models.Range(lte=learner_grade),
            )
        )

    if country_code is not None:
        filter_conditions.append(
            models.FieldCondition(
                key="country_code",
                match=models.MatchValue(
                    value=country_code.strip().upper()
                ),
            )
        )
        filter_conditions.append(
            models.FieldCondition(
                key="source_status",
                match=models.MatchValue(value="reviewed"),
            )
        )

    query_filter = (
        models.Filter(must=filter_conditions)
        if filter_conditions
        else None
    )

    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=question_vector,
        query_filter=query_filter,
        limit=limit,
        score_threshold=MINIMUM_RELEVANCE_SCORE,
        with_payload=True,
    ).points

    return [
        {
            "score": round(float(result.score), 4),
            "topic": result.payload.get("topic"),
            "grade": result.payload.get("grade"),
            "title": result.payload.get("title"),
            "content": result.payload.get("content"),
            "country_code": result.payload.get("country_code"),
            "curriculum_name": result.payload.get("curriculum_name"),
            "curriculum_version": result.payload.get("curriculum_version"),
            "source_title": result.payload.get("source_title"),
            "source_url": result.payload.get("source_url"),
            "source_page": result.payload.get("source_page"),
            "source_license": result.payload.get("source_license"),
            "source_status": result.payload.get("source_status"),
        }
        for result in results
    ]


def clean_optional_value(value: Any) -> str | None:
    if pd.isna(value):
        return None

    normalized = str(value).strip()
    return normalized or None
