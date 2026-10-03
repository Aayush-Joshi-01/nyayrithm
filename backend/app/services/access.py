from __future__ import annotations

from uuid import UUID

from app.core.auth import AuthenticatedUser
from app.core.exceptions import ForbiddenError, NoOrganizationError, NotFoundError
from app.db.factory import get_repository
from app.db.stores import Stores
from app.models.agent import AgentDefinition
from app.models.case import Case
from app.models.evidence import Evidence
from app.models.simulation import Simulation


class AccessService:
    """Resolves resources on behalf of a user acting for a firm, and enforces who sees what.

    Cases belong to a firm. Inside it, owners and admins see every case; an attorney sees
    the cases they created plus those explicitly shared with them. Simulations, evidence,
    agents and turns inherit access from their case. Anything the caller may not see is
    reported as *not found* (404), so ids cannot be probed, and a platform administrator
    has no access to case data at all.
    """

    def __init__(self, stores: Stores, user: AuthenticatedUser) -> None:
        self.stores = stores
        self.user = user

    def _repo(self, model: str):
        return get_repository(model, self.stores)

    @property
    def org_id(self) -> str:
        if not self.user.org_id:
            raise NoOrganizationError()
        return self.user.org_id

    async def _is_shared_with_me(self, case_id: UUID | str) -> bool:
        return await self._repo("case_member").count(
            {"case_id": str(case_id), "user_id": self.user.id}
        ) > 0

    async def _can_see(self, case: Case) -> bool:
        if not self.user.org_id or str(case.org_id) != self.user.org_id:
            return False
        if self.user.is_firm_manager or case.created_by == self.user.id:
            return True
        return await self._is_shared_with_me(case.id)

    def can_manage(self, case: Case) -> bool:
        """Delete or share a case: firm owners/admins, or the attorney who created it."""
        return self.user.is_firm_manager or case.created_by == self.user.id

    async def case(self, case_id: UUID | str) -> Case:
        case = await self._repo("case").get(str(case_id))
        if case is None or not await self._can_see(case):
            raise NotFoundError("Case", str(case_id))
        return case

    async def managed_case(self, case_id: UUID | str) -> Case:
        case = await self.case(case_id)
        if not self.can_manage(case):
            raise ForbiddenError("Only the case's creator or a firm admin can do this.")
        return case

    async def simulation(self, sim_id: UUID | str) -> Simulation:
        sim = await self._repo("simulation").get(str(sim_id))
        if sim is None:
            raise NotFoundError("Simulation", str(sim_id))
        try:
            await self.case(sim.case_id)
        except NotFoundError:
            raise NotFoundError("Simulation", str(sim_id)) from None
        return sim

    async def evidence(self, case_id: UUID | str, evidence_id: UUID | str) -> Evidence:
        await self.case(case_id)
        ev = await self._repo("evidence").get(str(evidence_id))
        if ev is None or str(ev.case_id) != str(case_id):
            raise NotFoundError("Evidence", str(evidence_id))
        return ev

    async def agent(self, agent_id: UUID | str) -> AgentDefinition:
        agent = await self._repo("agent").get(str(agent_id))
        if agent is None:
            raise NotFoundError("Agent", str(agent_id))
        try:
            await self.simulation(agent.simulation_id)
        except NotFoundError:
            raise NotFoundError("Agent", str(agent_id)) from None
        return agent
