import os

import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "320"))
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "300"))


def test_ollama_connection() -> dict:
    """Return the models currently installed in Ollama."""

    try:
        response = requests.get(
            f"{OLLAMA_URL}/api/tags",
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        models = [
            model.get("name")
            for model in data.get("models", [])
            if model.get("name")
        ]

        return {
            "connected": True,
            "models": models,
        }

    except requests.RequestException as error:
        return {
            "connected": False,
            "error": str(error),
        }


def generate_response(prompt: str) -> str:
    """Send a prompt to the configured Ollama model."""

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": OLLAMA_NUM_PREDICT,
            "temperature": 0.2,
        },
    }

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            timeout=OLLAMA_TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()
        return data.get("response", "").strip()

    except requests.Timeout as error:
        raise RuntimeError(
            "Ollama took too long to respond. The model may still be loading."
        ) from error

    except requests.RequestException as error:
        raise RuntimeError(
            f"Could not communicate with Ollama: {error}"
        ) from error
