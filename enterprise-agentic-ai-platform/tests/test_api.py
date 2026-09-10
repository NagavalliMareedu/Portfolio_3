from fastapi.testclient import TestClient

from app.main import app, orchestrator

client = TestClient(app)


def setup_function() -> None:
    orchestrator.approvals.clear()


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_grounded_question_returns_citation() -> None:
    response = client.post("/v1/runs", json={
        "query": "What is the refund policy?",
        "user_id": "user-1",
        "roles": ["employee"],
    })
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "completed"
    assert body["citations"][0]["source_id"] == "POL-REFUND-001"


def test_sensitive_tool_requires_role() -> None:
    response = client.post("/v1/runs", json={
        "query": "Create a refund for ORD-100",
        "user_id": "user-1",
        "roles": ["employee"],
    })
    assert response.status_code == 403


def test_sensitive_tool_pauses_and_resumes() -> None:
    run = client.post("/v1/runs", json={
        "query": "Create a refund for ORD-100",
        "user_id": "agent-1",
        "roles": ["support"],
    })
    assert run.status_code == 200
    assert run.json()["status"] == "pending_approval"
    approval_id = run.json()["approval_id"]

    decision = client.post(f"/v1/approvals/{approval_id}", json={
        "approved": True,
        "reviewer_id": "manager-1",
    })
    assert decision.status_code == 200
    assert decision.json()["status"] == "completed"
    assert "submitted" in decision.json()["answer"]


def test_rejected_action_is_not_executed() -> None:
    run = client.post("/v1/runs", json={
        "query": "Issue a refund for ORD-200",
        "user_id": "agent-1",
        "roles": ["support"],
    })
    approval_id = run.json()["approval_id"]
    decision = client.post(f"/v1/approvals/{approval_id}", json={
        "approved": False,
        "reviewer_id": "manager-1",
    })
    assert decision.json()["status"] == "rejected"
    assert decision.json()["answer"] is None
