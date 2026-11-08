import os
from typing import Any

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT = float(os.getenv("TUTOR_REQUEST_TIMEOUT", "330"))


st.set_page_config(
    page_title="G-RAFT Mathematics Tutor",
    page_icon="📘",
    layout="centered",
)


def ask_tutor(
    question: str,
    learner_grade: int,
    result_limit: int = 3,
) -> dict[str, Any]:
    """Send a mathematics question to the FastAPI backend."""

    response = requests.post(
        f"{API_URL}/tutor/ask",
        json={
            "question": question,
            "learner_grade": learner_grade,
            "result_limit": result_limit,
        },
        timeout=REQUEST_TIMEOUT,
    )

    try:
        data = response.json()
    except requests.JSONDecodeError as error:
        raise RuntimeError(
            "The backend returned an invalid response."
        ) from error

    if not response.ok:
        detail = data.get(
            "detail",
            "The mathematics tutor could not answer the question.",
        )
        raise RuntimeError(str(detail))

    return data


st.title("📘 G-RAFT Mathematics Tutor")

st.write(
    """
    Ask a primary mathematics question and receive a simple,
    curriculum-grounded explanation.
    """
)

with st.sidebar:
    st.header("Learner settings")

    learner_grade = st.selectbox(
        "Select the learner's class",
        options=list(range(1, 8)),
        index=2,
        format_func=lambda grade: f"Primary {grade}",
    )

    result_limit = st.slider(
        "Number of learning materials to retrieve",
        min_value=1,
        max_value=5,
        value=3,
    )

    show_sources = st.checkbox(
        "Show retrieved curriculum information",
        value=False,
    )

    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()


if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if (
            message["role"] == "assistant"
            and show_sources
            and message.get("metadata")
        ):
            metadata = message["metadata"]

            with st.expander("View curriculum sources"):
                topic = metadata.get("detected_topic")

                if topic:
                    st.write(f"**Detected topic:** {topic}")

                graph_context = metadata.get("graph_context")

                if graph_context:
                    st.write("### Knowledge graph context")
                    st.json(graph_context)

                retrieval_trace = metadata.get("retrieval_trace")

                if retrieval_trace:
                    st.write("### Retrieval trace")
                    st.json(retrieval_trace)

                materials = metadata.get("retrieved_materials", [])

                if materials:
                    st.write("### Retrieved learning materials")

                    for material in materials:
                        st.write(
                            f"**{material.get('title', 'Learning material')}**"
                        )
                        st.write(material.get("content", ""))
                        st.caption(
                            f"Topic: {material.get('topic')} | "
                            f"Score: {material.get('score')}"
                        )


question = st.chat_input(
    "Ask a mathematics question..."
)

if question:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"), st.spinner(
        "Searching the curriculum and preparing an explanation..."
    ):
        try:
            result = ask_tutor(
                question=question,
                learner_grade=learner_grade,
                result_limit=result_limit,
            )

            answer = result.get(
                "answer",
                "I could not generate an answer.",
            )

            st.markdown(answer)

            verification = result.get("verification")
            if verification:
                status = verification.get("status")
                if verification.get("check") == "evidence_references":
                    reference_status = verification.get("reference_status")
                    if reference_status == "passed":
                        st.info(
                            "Evidence references are valid; this does not "
                            "verify that the evidence supports every claim."
                        )
                    elif reference_status == "failed":
                        st.warning(
                            "Evidence citation check failed after "
                            f"{verification.get('refinement_attempts', 0)} "
                            "correction attempt(s). Claim accuracy is not "
                            "verified."
                        )
                    else:
                        st.info(
                            "No retrieved evidence was available. This answer "
                            "was not generated from curriculum evidence."
                        )
                elif status == "passed":
                    st.success(
                        "Arithmetic result check passed. "
                        "This does not verify the full explanation."
                    )
                elif status == "failed":
                    st.warning(
                        "The arithmetic result check did not pass. "
                        "Please review the answer."
                    )
                else:
                    st.info(
                        "This answer was not checked by the arithmetic "
                        "verifier; that does not mean it is verified."
                    )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                    "metadata": {
                        "verification": verification,
                        "detected_topic": result.get(
                            "detected_topic"
                        ),
                        "graph_context": result.get(
                            "graph_context"
                        ),
                        "retrieved_materials": result.get(
                            "retrieved_materials",
                            [],
                        ),
                        "retrieval_trace": result.get("retrieval_trace"),
                    },
                }
            )

            if show_sources:
                with st.expander("View curriculum sources"):
                    if verification:
                        st.write("### Verification")
                        st.json(verification)

                    if result.get("detected_topic"):
                        st.write(
                            "**Detected topic:** "
                            f"{result['detected_topic']}"
                        )

                    if result.get("graph_context"):
                        st.write("### Knowledge graph evidence [G1]")
                        st.json(result["graph_context"])

                    if result.get("retrieval_trace"):
                        st.write("### Retrieval trace")
                        st.json(result["retrieval_trace"])

                    materials = result.get(
                        "retrieved_materials",
                        [],
                    )

                    if materials:
                        st.write(
                            "### Retrieved learning materials"
                        )

                        for index, material in enumerate(materials, start=1):
                            st.caption(f"Evidence [M{index}]")
                            st.write(
                                f"**{material.get('title')}**"
                            )
                            st.write(
                                material.get("content", "")
                            )
                            st.caption(
                                f"Topic: "
                                f"{material.get('topic')} | "
                                f"Score: "
                                f"{material.get('score')}"
                            )

        except requests.ConnectionError:
            st.error(
                "The FastAPI backend is not running. "
                "Start it using uvicorn backend.main:app --reload."
            )

        except requests.Timeout:
            st.error(
                "The model took too long to respond. "
                "Check that the Ollama container is running."
            )

        except RuntimeError as error:
            st.error(str(error))

        except requests.RequestException as error:
            st.error(
                f"Could not communicate with the backend: {error}"
            )
