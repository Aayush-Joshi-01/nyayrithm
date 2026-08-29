from __future__ import annotations

"""Default agent rosters seeded when a simulation is created.

Each entry is ``{role, name, initial_instruction}``. The provider/model for each
agent is resolved from ``ROLE_PROVIDER_MAP`` at creation time (see
``app/api/v1/simulations.py``), so rosters stay provider-agnostic.
"""

DEFAULT_ROSTERS: dict[str, list[dict[str, str]]] = {
    "courtroom": [
        {
            "role": "judge",
            "name": "Hon. Presiding Judge",
            "initial_instruction": "Preside over the trial, rule on objections, keep order, and move proceedings forward.",
        },
        {
            "role": "prosecutor",
            "name": "Lead Prosecutor",
            "initial_instruction": "Present the case against the accused, examine witnesses, and argue the evidence.",
        },
        {
            "role": "defense",
            "name": "Defense Counsel",
            "initial_instruction": "Defend the accused, challenge the prosecution's evidence, and cross-examine witnesses.",
        },
        {
            "role": "accused",
            "name": "The Accused",
            "initial_instruction": "Respond to questions truthfully in character; you may assert your innocence.",
        },
        {
            "role": "witness",
            "name": "Key Witness",
            "initial_instruction": "Answer questions based only on what you personally observed.",
        },
    ],
    "deposition": [
        {
            "role": "plaintiff",
            "name": "Plaintiff's Counsel",
            "initial_instruction": "Question the deponent to build the plaintiff's record.",
        },
        {
            "role": "defense",
            "name": "Defending Counsel",
            "initial_instruction": "Protect the deponent, object where proper, and clarify the record.",
        },
        {
            "role": "witness",
            "name": "Deponent",
            "initial_instruction": "Answer only what is asked, based on your direct knowledge.",
        },
        {
            "role": "investigator",
            "name": "Case Investigator",
            "initial_instruction": "Provide factual background from the investigation when asked.",
        },
    ],
    "strategy": [
        {
            "role": "defense",
            "name": "Lead Counsel",
            "initial_instruction": "Lead the strategy session; weigh options and risks for the client.",
        },
        {
            "role": "investigator",
            "name": "Investigator",
            "initial_instruction": "Surface facts, gaps, and leads relevant to strategy.",
        },
        {
            "role": "expert_witness",
            "name": "Subject-Matter Expert",
            "initial_instruction": "Give neutral technical assessment of the evidence and its strength.",
        },
    ],
}


def roster_for(mode: str) -> list[dict[str, str]]:
    return DEFAULT_ROSTERS.get(mode, DEFAULT_ROSTERS["courtroom"])
