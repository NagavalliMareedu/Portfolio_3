import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Plan:
    intent: str
    tool_name: str | None = None
    arguments: dict[str, Any] | None = None


class Planner:
    """Deterministic planner used for a safe, locally runnable demo."""

    def plan(self, query: str) -> Plan:
        order_match = re.search(r"\bORD-\d{3,10}\b", query.upper())
        arguments = {"order_id": order_match.group(0)} if order_match else {}
        lowered = query.lower()
        if "refund" in lowered and any(word in lowered for word in ("create", "issue", "submit")):
            return Plan("create_refund", "create_refund", arguments)
        if order_match and any(word in lowered for word in ("where", "status", "track", "lookup")):
            return Plan("lookup_order", "lookup_order", arguments)
        return Plan("knowledge_question")
