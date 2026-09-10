from uuid import uuid4

from app.approvals import ApprovalStore
from app.knowledge import KnowledgeBase
from app.models import ApprovalRecord, Citation, RunRequest, RunResponse, RunStatus, TraceEvent
from app.planner import Planner
from app.tools import TOOLS, execute_tool


class AgentOrchestrator:
    def __init__(
        self,
        knowledge_base: KnowledgeBase | None = None,
        planner: Planner | None = None,
        approvals: ApprovalStore | None = None,
    ) -> None:
        self.knowledge_base = knowledge_base or KnowledgeBase()
        self.planner = planner or Planner()
        self.approvals = approvals or ApprovalStore()

    def run(self, request: RunRequest) -> RunResponse:
        run_id = str(uuid4())
        trace = [TraceEvent(step="request", detail="Input validated")]
        plan = self.planner.plan(request.query)
        trace.append(TraceEvent(step="planner", detail=f"Intent: {plan.intent}"))
        citations = self.knowledge_base.search(request.query)
        trace.append(TraceEvent(step="retriever", detail=f"Retrieved {len(citations)} sources"))

        if plan.tool_name is None:
            answer = self._grounded_answer(request.query, citations)
            trace.append(TraceEvent(step="response", detail="Grounded answer composed"))
            return RunResponse(
                run_id=run_id, status=RunStatus.COMPLETED, answer=answer,
                citations=citations, trace=trace,
            )

        definition = TOOLS[plan.tool_name]
        if definition.required_role not in request.roles:
            raise PermissionError(f"Role '{definition.required_role}' is required")
        if definition.requires_approval:
            approval_id = str(uuid4())
            self.approvals.save(ApprovalRecord(
                approval_id=approval_id, run_id=run_id, user_id=request.user_id,
                tool_name=plan.tool_name, arguments=plan.arguments or {}, query=request.query,
                roles=request.roles,
            ))
            trace.append(TraceEvent(step="approval", detail="Sensitive action paused"))
            return RunResponse(
                run_id=run_id, status=RunStatus.PENDING_APPROVAL,
                citations=citations, trace=trace, approval_id=approval_id,
            )

        result = execute_tool(plan.tool_name, plan.arguments or {}, request.roles)
        trace.append(TraceEvent(step="tool", detail=f"Executed {plan.tool_name}"))
        return RunResponse(
            run_id=run_id, status=RunStatus.COMPLETED,
            answer=f"Tool result: {result}", citations=citations, trace=trace,
        )

    def resume(self, approval_id: str, approved: bool, reviewer_id: str) -> RunResponse:
        record = self.approvals.get(approval_id)
        if record is None:
            raise KeyError("Approval request not found")
        if record.decided:
            raise ValueError("Approval request has already been decided")
        record.decided = True
        record.approved = approved
        record.reviewer_id = reviewer_id
        trace = [TraceEvent(step="approval", detail=f"Decision recorded by {reviewer_id}")]
        if not approved:
            return RunResponse(run_id=record.run_id, status=RunStatus.REJECTED, trace=trace)
        result = execute_tool(record.tool_name, record.arguments, record.roles)
        trace.append(TraceEvent(step="tool", detail=f"Executed {record.tool_name}"))
        return RunResponse(
            run_id=record.run_id, status=RunStatus.COMPLETED,
            answer=f"Approved tool result: {result}", trace=trace,
        )

    @staticmethod
    def _grounded_answer(query: str, citations: list[Citation]) -> str:
        if not citations:
            return "I could not find grounded information for that request."
        evidence = " ".join(item.excerpt for item in citations[:2])
        sources = ", ".join(f"[{item.source_id}]" for item in citations[:2])
        return f"Based on the available policy: {evidence} Sources: {sources}"
