"""Invoice Management System (IMS) action model.

Ported from India Compliance's `gst_invoice_management_system` doctype and
`purchase_reconciliation_tool` status mapping, Resilient Tech, GPL v3.

IMS lets a buyer accept, reject, or defer each inward supply (GSTR-2A/2B line),
which drives ITC claims in GSTR-3B. This module defines the action vocabulary
and the transition semantics, independent of any storage backend.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ImsAction(str, Enum):
    NO_ACTION = "No Action"
    ACCEPT = "Accept"
    REJECT = "Reject"
    PENDING = "Pending"
    IGNORE = "Ignore"


# Ported status map: IMS/PR action -> reconciliation status.
ACTION_STATUS_MAP: dict[ImsAction, str] = {
    ImsAction.NO_ACTION: "Unreconciled",
    ImsAction.ACCEPT: "Reconciled",
    ImsAction.REJECT: "Unreconciled",
    ImsAction.PENDING: "Unreconciled",
    ImsAction.IGNORE: "Ignored",
}


#: Actions that are "resolved" and should be excluded from the active queue.
RESOLVED_ACTIONS = (ImsAction.ACCEPT, ImsAction.IGNORE)


@dataclass(frozen=True)
class ImsDecision:
    """A single applied IMS action, with reviewer context."""

    packet_id: str
    action: ImsAction
    reviewer_id: str = "system"
    comments: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def status(self) -> str:
        return ACTION_STATUS_MAP[self.action]

    @property
    def is_resolved(self) -> bool:
        return self.action in RESOLVED_ACTIONS

    def to_dict(self) -> dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "action": self.action.value,
            "status": self.status,
            "reviewer_id": self.reviewer_id,
            "comments": self.comments,
            "updated_at": self.updated_at,
        }


def apply_action(
    packet_id: str,
    action: ImsAction | str,
    reviewer_id: str = "system",
    comments: str = "",
) -> ImsDecision:
    """Normalize and apply an IMS action to a packet ID."""
    if isinstance(action, str):
        action = ImsAction(action)
    return ImsDecision(
        packet_id=packet_id,
        action=action,
        reviewer_id=reviewer_id,
        comments=comments,
    )
