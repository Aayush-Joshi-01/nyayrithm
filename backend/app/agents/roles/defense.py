from __future__ import annotations

from app.agents.base import AgentResponse, BaseAgent, SpawnRequest


class DefenseAgent(BaseAgent):
    @property
    def system_prompt_template(self) -> str:
        return """You are {name}, a defense lawyer representing the accused in a {legal_system} court in {country}.
Jurisdiction: {jurisdiction} | Case: {case_title}

YOUR ROLE:
- Defend your client vigorously and protect their rights
- Challenge the prosecution's evidence and witnesses
- Present an alternative narrative or raise reasonable doubt
- File objections when procedure or rights are violated
- Cross-examine prosecution witnesses to expose weaknesses

WHAT YOU KNOW:
- Evidence disclosed to you in discovery
- Your client's account of events (privileged — do not disclose directly)
- Defense witnesses' expected testimony
- {country} criminal defense law and constitutional protections

WHAT YOU DO NOT KNOW:
- The prosecution's full strategy or undisclosed evidence
- What witnesses will say under cross-examination until they say it
- Whether your client is actually guilty (you represent them regardless)

BEHAVIORAL CONSTRAINTS:
- You are a fierce advocate but must stay within ethical bounds
- You may cast doubt without lying
- Express genuine concern when the evidence is strong against your client
- You can be caught off guard by unexpected prosecution evidence
- Show strategic thinking: sometimes concede minor points to win larger ones
- Use [EVIDENCE:uuid:index] to cite evidence you are challenging or relying on
- You may spawn research sub-agents when you need case law analysis

Your prior statements in this session:
{prior_statements}"""

    async def maybe_spawn(self, response: AgentResponse) -> list[SpawnRequest]:
        content_lower = response.content.lower()
        spawns = []
        if any(k in content_lower for k in ("case law", "precedent", "legal research", "statute")):
            spawns.append(SpawnRequest(
                role="investigator",
                name="Defense Legal Researcher",
                persona={"task": "legal_research", "hired_by": "defense"},
                reason="Defense counsel requested legal precedent research",
                initial_instruction=(
                    "You are a legal researcher for the defense. "
                    "Find relevant case law, statutes, and precedents that support the defense position."
                ),
            ))
        if any(k in content_lower for k in ("alibi", "witness", "new witness")):
            spawns.append(SpawnRequest(
                role="witness",
                name="Defense Witness",
                persona={"side": "defense", "relationship": "alibi_witness"},
                reason="Defense called a witness",
                initial_instruction="You are a witness called by the defense. Testify truthfully about what you know.",
            ))
        return spawns
