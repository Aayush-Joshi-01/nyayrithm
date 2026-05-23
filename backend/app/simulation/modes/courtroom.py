from __future__ import annotations

from typing import Any


class CourtroomMode:
    """
    Turn order: Judge → Prosecutor → Defense → Witnesses (rotation)
    Judge can interject at any point; objections are routed to Judge.
    """
    mode_name = "courtroom"

    def get_config_defaults(self) -> dict[str, Any]:
        return {
            "allow_judge_interjection": True,
            "objection_routing": "judge",
            "opening_statements": True,
            "closing_arguments": True,
        }

    def get_preferred_role_order(self) -> list[str]:
        return ["judge", "prosecutor", "witness", "defense", "expert_witness", "investigator"]
