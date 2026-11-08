from backend import hybrid_tutor_service


def test_answer_uses_detected_topic_and_requested_grade(monkeypatch):
    search_arguments = {}
    materials = [
        {
            "id": 17,
            "score": 0.91,
            "topic": "Addition",
            "grade": 1,
            "title": "Joining groups",
            "content": "Addition joins quantities.",
            "country_code": "UG",
            "curriculum_name": "Uganda Primary",
            "curriculum_version": "2025",
            "source_title": "Mathematics curriculum",
            "source_url": "https://example.test/curriculum",
            "source_page": "12",
            "source_license": "Permission granted",
            "source_status": "reviewed",
        }
    ]
    topic = {
        "topic": "Addition",
        "node_id": "topic_addition",
        "description": "Combining quantities.",
        "grade": 1,
        "difficulty": "beginner",
        "formula": "a + b = c",
        "prerequisites": ["Counting"],
        "next_topics": ["Subtraction"],
    }
    def fake_search(**arguments):
        search_arguments.update(arguments)
        return materials

    monkeypatch.setattr(hybrid_tutor_service, "search_materials", fake_search)
    monkeypatch.setattr(
        hybrid_tutor_service,
        "get_topic_details",
        lambda _: topic,
    )
    prompts = []

    def fake_generate(prompt):
        prompts.append(prompt)
        return "Addition joins quantities [M1]."

    monkeypatch.setattr(hybrid_tutor_service, "generate_response", fake_generate)

    result = hybrid_tutor_service.answer_math_question(
        "How do I add?",
        learner_grade=2,
    )

    assert result["detected_topic"] == "Addition"
    assert result["learner_grade"] == 2
    assert result["answer"] == "Addition joins quantities [M1]."
    assert result["verification"]["status"] == "not_checked"
    assert result["verification"]["check"] == "evidence_references"
    assert result["verification"]["reference_status"] == "passed"
    assert result["verification"]["refinement_attempts"] == 0
    assert "[M1]" in prompts[0]
    assert "[G1]" in prompts[0]
    assert search_arguments["learner_grade"] == 2
    vector_trace = result["retrieval_trace"]["vector_search"]
    assert vector_trace["status"] == "completed"
    assert vector_trace["hit_count"] == 1
    assert vector_trace["filters"]["maximum_grade"] == 2
    assert vector_trace["hits"][0]["id"] == 17
    assert vector_trace["hits"][0]["source_page"] == "12"
    assert result["retrieval_trace"]["graph_lookup"] == {
        "status": "found",
        "query_topic": "Addition",
        "node_id": "topic_addition",
        "topic": "Addition",
        "provenance_status": "not_recorded",
    }


def test_country_scoped_answer_does_not_use_unscoped_graph(monkeypatch):
    search_arguments = {}

    def fake_search(**arguments):
        search_arguments.update(arguments)
        return []

    def fail_if_called(_):
        raise AssertionError("Country-scoped answers must not use unscoped graph data")

    monkeypatch.setattr(hybrid_tutor_service, "search_materials", fake_search)
    monkeypatch.setattr(hybrid_tutor_service, "get_topic_details", fail_if_called)
    def fail_if_called(_):
        raise AssertionError("Generation must not run without supporting evidence")

    monkeypatch.setattr(hybrid_tutor_service, "generate_response", fail_if_called)

    result = hybrid_tutor_service.answer_math_question(
        "How do I add?",
        country_code="UG",
    )

    assert search_arguments["country_code"] == "UG"
    assert result["country_code"] == "UG"
    assert result["graph_context"] is None
    trace = result["retrieval_trace"]
    assert trace["vector_search"]["filters"]["country_code"] == "UG"
    assert trace["vector_search"]["filters"]["required_source_status"] == "reviewed"
    assert trace["vector_search"]["hit_count"] == 0
    assert trace["graph_lookup"]["status"] == "skipped_country_scope"
    assert result["verification"]["reference_status"] == "not_checkable"


def test_empty_vector_search_is_recorded_without_graph_lookup(monkeypatch):
    monkeypatch.setattr(
        hybrid_tutor_service,
        "search_materials",
        lambda **_: [],
    )
    def fail_if_called(_):
        raise AssertionError("Generation must not run without supporting evidence")

    monkeypatch.setattr(hybrid_tutor_service, "generate_response", fail_if_called)

    result = hybrid_tutor_service.answer_math_question("Explain fractions.")

    trace = result["retrieval_trace"]
    assert trace["vector_search"]["status"] == "completed"
    assert trace["vector_search"]["hit_count"] == 0
    assert trace["vector_search"]["hits"] == []
    assert result["verification"]["reference_status"] == "not_checkable"
    assert trace["graph_lookup"] == {
        "status": "skipped_no_detected_topic",
        "query_topic": None,
        "node_id": None,
        "topic": None,
        "provenance_status": "not_applicable",
    }


def test_explicit_arithmetic_bypasses_external_services(monkeypatch):
    def fail_if_called(**_):
        raise AssertionError("Retrieval should not run for explicit arithmetic")

    monkeypatch.setattr(hybrid_tutor_service, "search_materials", fail_if_called)
    monkeypatch.setattr(hybrid_tutor_service, "generate_response", fail_if_called)

    result = hybrid_tutor_service.answer_math_question(
        "What is 12 / 3?",
        learner_grade=2,
    )

    assert result["verified_calculation"]["result"] == "4"
    assert result["verification"]["status"] == "passed"
    assert result["verification"]["expected_result"] == "4"
    assert result["detected_topic"] == "Division"
    assert "12 ÷ 3 = 4" in result["answer"]
    assert (
        result["retrieval_trace"]["vector_search"]["status"]
        == "not_run_deterministic_arithmetic"
    )


def test_arithmetic_verification_failure_is_returned(monkeypatch):
    monkeypatch.setattr(
        hybrid_tutor_service,
        "build_calculation_answer",
        lambda _: "The answer is 5.",
    )

    result = hybrid_tutor_service.answer_math_question("What is 12 / 3?")

    assert result["answer"] == "The answer is 5."
    assert result["verification"]["status"] == "failed"
    assert result["verification"]["expected_result"] == "4"


def test_missing_citations_trigger_one_refinement(monkeypatch):
    responses = iter(
        [
            "Addition joins quantities.",
            "Addition joins quantities [M1].",
        ]
    )
    prompts = []

    monkeypatch.setattr(
        hybrid_tutor_service,
        "search_materials",
        lambda **_: [{"topic": "Addition", "content": "Addition joins quantities."}],
    )
    monkeypatch.setattr(hybrid_tutor_service, "get_topic_details", lambda _: None)
    monkeypatch.setattr(
        hybrid_tutor_service,
        "generate_response",
        lambda prompt: prompts.append(prompt) or next(responses),
    )

    result = hybrid_tutor_service.answer_math_question("Explain addition.")

    assert result["answer"] == "Addition joins quantities [M1]."
    assert result["verification"]["reference_status"] == "passed"
    assert result["verification"]["refinement_attempts"] == 1
    assert len(prompts) == 2
    assert "Sentences without a citation: 1" in prompts[1]


def test_failed_citation_refinement_is_reported_without_claiming_verification(
    monkeypatch,
):
    responses = iter(
        [
            "Addition joins quantities [M9].",
            "Addition joins quantities [M8].",
        ]
    )
    monkeypatch.setattr(
        hybrid_tutor_service,
        "search_materials",
        lambda **_: [{"topic": "Addition", "content": "Addition joins quantities."}],
    )
    monkeypatch.setattr(hybrid_tutor_service, "get_topic_details", lambda _: None)
    monkeypatch.setattr(
        hybrid_tutor_service,
        "generate_response",
        lambda _: next(responses),
    )

    result = hybrid_tutor_service.answer_math_question("Explain addition.")

    assert result["answer"] == (
        "I couldn't produce an answer with checkable evidence references. "
        "Please try asking in a different way."
    )
    assert result["verification"]["status"] == "not_checked"
    assert result["verification"]["reference_status"] == "failed"
    assert result["verification"]["invalid_references"] == ["M8"]
    assert result["verification"]["refinement_attempts"] == 1
