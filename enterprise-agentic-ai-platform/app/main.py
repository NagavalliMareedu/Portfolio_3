from fastapi import FastAPI, HTTPException

from app.models import ApprovalDecision, ApprovalRecord, RunRequest, RunResponse
from app.orchestrator import AgentOrchestrator
from app.tools import ToolError

app = FastAPI(
    title="Enterprise Agentic AI Platform",
    version="0.1.0",
    description="Auditable agent workflow with retrieval, tools, RBAC, and human approval.",
)
orchestrator = AgentOrchestrator()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/runs", response_model=RunResponse)
def create_run(request: RunRequest) -> RunResponse:
    try:
        return orchestrator.run(request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ToolError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/v1/approvals/{approval_id}", response_model=ApprovalRecord)
def get_approval(approval_id: str) -> ApprovalRecord:
    record = orchestrator.approvals.get(approval_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return record


@app.post("/v1/approvals/{approval_id}", response_model=RunResponse)
def decide_approval(approval_id: str, decision: ApprovalDecision) -> RunResponse:
    try:
        return orchestrator.resume(approval_id, decision.approved, decision.reviewer_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (PermissionError, ToolError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
