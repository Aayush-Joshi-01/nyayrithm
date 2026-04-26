from __future__ import annotations

from typing import Any


class StrategyMode:
    """
    Internal strategy discussion — no judge, free-form turn order.
    Sub-agents spawn freely for legal research, analysis.
    """
    mode_name = "strategy"

    def get_config_defaults(self) -> dict[str, Any]:
        return {
            "free_form": True,
            "allow_research_agents": True,
            "private_to_side": "defense",  # or "prosecution"
        }

    def get_preferred_role_order(self) -> list[str]:
        return ["defense", "investigator", "expert_witness", "plaintiff", "accused"]
