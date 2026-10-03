from __future__ import annotations

import sqlite3
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

import pytest

from app.db.session import get_session
from app.legal.audit import GENESIS_HASH, AuditLog, compute_hash, sha256_text, verify_chain
from app.models.audit import AuditEvent

SIM = uuid4()


def make_chain(n: int = 4) -> list[AuditEvent]:
    events: list[AuditEvent] = []
    prev = GENESIS_HASH
    for seq in range(n):
        payload = {"turn_number": seq, "note": "résumé ✓"}
        h = compute_hash(str(SIM), seq, "turn.generated", "agent:a", payload, prev)
        events.append(AuditEvent(
            simulation_id=SIM, seq=seq, event_type="turn.generated", actor="agent:a",
            payload=payload, prev_hash=prev, hash=h,
        ))
        prev = h
    return events


def test_intact_chain_verifies():
    result = verify_chain(make_chain())
    assert result["valid"] and result["events"] == 4
    assert result["head_hash"] == make_chain()[-1].hash


def test_empty_chain_is_valid_with_no_head():
    assert verify_chain([]) == {
        "valid": True, "events": 0, "broken_at": None, "reason": None, "head_hash": None,
    }


def test_edited_payload_is_detected_at_the_edited_event():
    chain = make_chain()
    chain[2].payload = {**chain[2].payload, "turn_number": 999}
    result = verify_chain(chain)
    assert not result["valid"] and result["broken_at"] == 2
    assert "hash" in result["reason"]


def test_edited_actor_or_type_is_detected():
    for field, value in (("actor", "user:mallory"), ("event_type", "turn.edited")):
        chain = make_chain()
        setattr(chain[1], field, value)
        assert verify_chain(chain)["broken_at"] == 1


def test_deleted_event_is_detected():
    chain = make_chain()
    del chain[1]
    result = verify_chain(chain)
    assert not result["valid"] and result["broken_at"] == 2
    assert "missing or reordered" in result["reason"]


def test_reordered_events_are_detected():
    chain = make_chain()
    chain[1], chain[2] = chain[2], chain[1]
    assert not verify_chain(chain)["valid"]


def test_truncating_the_tail_is_not_detectable_by_the_chain_alone():
    # Documented limitation: the head hash must be anchored elsewhere to catch this.
    chain = make_chain()[:2]
    assert verify_chain(chain)["valid"]


def test_rewriting_a_hash_consistently_breaks_the_next_link():
    chain = make_chain()
    chain[1].payload = {"turn_number": 1, "note": "forged"}
    chain[1].hash = compute_hash(
        str(SIM), 1, chain[1].event_type, chain[1].actor, chain[1].payload, chain[1].prev_hash
    )
    result = verify_chain(chain)
    assert result["broken_at"] == 2 and "previous-hash" in result["reason"]


def test_hash_is_independent_of_dict_key_order():
    a = compute_hash("s", 0, "e", "x", {"a": 1, "b": 2}, GENESIS_HASH)
    b = compute_hash("s", 0, "e", "x", {"b": 2, "a": 1}, GENESIS_HASH)
    assert a == b


def test_sha256_text_is_stable():
    assert sha256_text("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


# ── persisted log ─────────────────────────────────────────────────────────────
async def test_log_appends_a_linked_chain_and_verifies(db_path: Path):
    sim = str(uuid4())
    async for session in get_session():
        log = AuditLog(session)
        first = await log.append(sim, "simulation.started", "user:a", {"mode": "courtroom"})
        second = await log.append(sim, "turn.generated", "agent:x", {"turn_number": 0})
        third = await log.append(sim, "simulation.completed", "system", {"total_turns": 1})

        assert (first.seq, second.seq, third.seq) == (0, 1, 2)
        assert first.prev_hash == GENESIS_HASH
        assert second.prev_hash == first.hash and third.prev_hash == second.hash
        assert "ts" in first.payload

        verdict = await log.verify(sim)
        assert verdict["valid"] and verdict["events"] == 3 and verdict["head_hash"] == third.hash


async def test_chains_are_independent_per_simulation(db_path: Path):
    a, b = str(uuid4()), str(uuid4())
    async for session in get_session():
        log = AuditLog(session)
        await log.append(a, "x", "u", {})
        await log.append(a, "y", "u", {})
        first_b = await log.append(b, "x", "u", {})
        assert first_b.seq == 0 and first_b.prev_hash == GENESIS_HASH


async def test_tampering_in_the_database_is_caught(db_path: Path):
    sim = str(uuid4())
    async for session in get_session():
        log = AuditLog(session)
        await log.append(sim, "simulation.started", "user:a", {"mode": "courtroom"})
        await log.append(sim, "turn.generated", "agent:x", {"turn_number": 0})
        await log.append(sim, "turn.generated", "agent:x", {"turn_number": 1})

    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE audit_events SET payload = ? WHERE seq = 1", ['{"turn_number": 42}'])
    conn.commit()
    conn.close()

    async for session in get_session():
        result = await AuditLog(session).verify(sim)
        assert not result["valid"] and result["broken_at"] == 1


async def test_pagination_does_not_hide_events_from_verification(db_path: Path):
    sim = str(uuid4())
    async for session in get_session():
        log = AuditLog(session)
        for i in range(7):
            await log.append(sim, "turn.generated", "agent:x", {"turn_number": i})
        page, total = await log.events(sim, page=2, size=3)
        assert total == 7 and [e.seq for e in page] == [3, 4, 5]
        assert (await log.verify(sim))["events"] == 7


def test_make_chain_helper_is_deterministic():
    assert deepcopy(make_chain())[0].hash == make_chain()[0].hash


@pytest.mark.parametrize("n", [1, 2, 25])
def test_chains_of_any_length_verify(n):
    assert verify_chain(make_chain(n))["valid"]
