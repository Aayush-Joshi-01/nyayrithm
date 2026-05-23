from __future__ import annotations

from typing import Any


class DepositionMode:
    """
    Turn order: Questioner (prosecutor/defense) → Witness alternation.
    No judge by default; others observe silently.
    """
    mode_name = "deposition"

    def get_config_defaults(self) -> dict[str, Any]:
        return {
            "questioner_role": "prosecutor",
            "deponent_role": "witness",
            "allow_objections": False,
            "transcript_mode": True,
        }

    def get_preferred_role_order(self) -> list[str]:
        return ["prosecutor", "witness", "defense", "plaintiff", "accused"]
