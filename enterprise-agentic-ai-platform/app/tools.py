import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


class ToolError(ValueError):
    pass


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    required_role: str
    requires_approval: bool
    handler: Callable[[dict[str, Any]], dict[str, Any]]


def lookup_order(arguments: dict[str, Any]) -> dict[str, Any]:
    order_id = str(arguments.get("order_id", "")).upper()
    if not re.fullmatch(r"ORD-\d{3,10}", order_id):
        raise ToolError("order_id must use the format ORD-100")
    return {"order_id": order_id, "status": "shipped", "eta": "3 business days"}


def create_refund(arguments: dict[str, Any]) -> dict[str, Any]:
    order_id = str(arguments.get("order_id", "")).upper()
    if not re.fullmatch(r"ORD-\d{3,10}", order_id):
        raise ToolError("order_id must use the format ORD-100")
    return {"order_id": order_id, "refund_status": "submitted", "audit_logged": True}


TOOLS = {
    "lookup_order": ToolDefinition("lookup_order", "employee", False, lookup_order),
    "create_refund": ToolDefinition("create_refund", "support", True, create_refund),
}


def execute_tool(name: str, arguments: dict[str, Any], roles: set[str]) -> dict[str, Any]:
    definition = TOOLS.get(name)
    if definition is None:
        raise ToolError(f"Unknown tool: {name}")
    if definition.required_role not in roles:
        raise PermissionError(f"Role '{definition.required_role}' is required for {name}")
    return definition.handler(arguments)
