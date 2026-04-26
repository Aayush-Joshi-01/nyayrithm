from app.agents.roles.judge import JudgeAgent
from app.agents.roles.prosecutor import ProsecutorAgent
from app.agents.roles.defense import DefenseAgent
from app.agents.roles.plaintiff import PlaintiffAgent
from app.agents.roles.accused import AccusedAgent
from app.agents.roles.witness import WitnessAgent
from app.agents.roles.investigator import InvestigatorAgent
from app.agents.roles.expert_witness import ExpertWitnessAgent

ROLE_AGENT_MAP = {
    "judge": JudgeAgent,
    "prosecutor": ProsecutorAgent,
    "defense": DefenseAgent,
    "plaintiff": PlaintiffAgent,
    "accused": AccusedAgent,
    "witness": WitnessAgent,
    "investigator": InvestigatorAgent,
    "expert_witness": ExpertWitnessAgent,
    "custom": WitnessAgent,  # default fallback for custom roles
}

__all__ = [
    "JudgeAgent", "ProsecutorAgent", "DefenseAgent", "PlaintiffAgent",
    "AccusedAgent", "WitnessAgent", "InvestigatorAgent", "ExpertWitnessAgent",
    "ROLE_AGENT_MAP",
]
