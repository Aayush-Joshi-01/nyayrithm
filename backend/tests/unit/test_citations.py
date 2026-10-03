from __future__ import annotations

import pytest

from app.legal.citations import extract_and_verify
from app.legal.corpus import get_corpus, normalise_party_name, normalise_section
from app.legal.review import LegalReviewer, correction_note_from


@pytest.fixture(scope="module")
def pack():
    p = get_corpus().get("IN")
    assert p is not None
    return p


def only(text: str, pack):
    found = extract_and_verify(text, pack)
    assert len(found) == 1, [c.raw for c in found]
    return found[0]


# ── statutes ──────────────────────────────────────────────────────────────────
def test_current_provision_is_verified(pack):
    c = only("The prosecution relies on Section 103 of the BNS for murder.", pack)
    assert (c.kind, c.status, c.severity) == ("statute", "verified", "ok")
    assert c.ref == "BNS 103"
    assert c.title == "Punishment for murder"


def test_repealed_ipc_section_points_to_its_successor(pack):
    c = only("He is charged under Section 302 IPC.", pack)
    assert c.status == "superseded"
    assert c.successor == "BNS 103"
    assert "repealed" in c.message and "BNS 103" in c.message
    assert c.severity == "notice"  # still valid for conduct before 1 July 2024


@pytest.mark.parametrize("text,successor", [
    ("IPC Section 420", "BNS 318"),
    ("u/s 498A IPC", "BNS 85"),
    ("Section 65B of the Indian Evidence Act", "BSA 63"),
    ("Section 438 of the Code of Criminal Procedure", "BNSS 482"),
    ("Section 313 CrPC", "BNSS 351"),
])
def test_old_act_forms_resolve_to_current_law(pack, text, successor):
    assert only(text, pack).successor == successor


def test_several_sections_in_one_citation(pack):
    found = extract_and_verify("Sections 302 and 34 IPC apply.", pack)
    assert [c.ref for c in found] == ["IPC 302", "IPC 34"]
    assert found[1].successor == "BNS 3"


def test_bare_acronym_form(pack):
    c = only("As BNS 103 provides.", pack)
    assert c.ref == "BNS 103" and c.status == "verified"


def test_subsection_does_not_change_the_section(pack):
    c = only("Section 63(1) of the BSA requires a certificate.", pack)
    assert c.ref == "BSA 63" and c.status == "verified"


def test_section_beyond_the_act_is_flagged_as_nonexistent(pack):
    c = only("Under Section 9999 of the BNS the accused is liable.", pack)
    assert (c.status, c.severity) == ("nonexistent", "error")
    assert "358" in c.message


def test_last_valid_section_is_in_range_but_unindexed(pack):
    c = only("Section 358 BNS", pack)
    assert c.status == "unindexed" and c.severity == "notice"


def test_year_after_act_name_is_not_a_section_number(pack):
    assert extract_and_verify("The Indian Evidence Act 1872 governs proof.", pack) == []
    assert extract_and_verify("Under the Code of Civil Procedure 1908 the court may...", pack) == []


def test_ordinary_words_are_not_mistaken_for_citations(pack):
    assert extract_and_verify("The cases were decided on section headings alone.", pack) == []
    assert extract_and_verify("The second sections of the road were closed.", pack) == []


def test_duplicate_citation_is_reported_once(pack):
    found = extract_and_verify("Section 103 BNS ... as I said, BNS 103 applies.", pack)
    assert len(found) == 1


# ── constitution ──────────────────────────────────────────────────────────────
def test_article_is_verified(pack):
    c = only("This violates Article 21 of the Constitution.", pack)
    assert (c.kind, c.status) == ("constitution", "verified")
    assert "life and personal liberty" in c.title


def test_article_list(pack):
    found = extract_and_verify("Articles 14, 19 and 21 are engaged.", pack)
    assert [c.ref for c in found] == ["COI Article 14", "COI Article 19", "COI Article 21"]


def test_article_with_clause(pack):
    assert only("Article 19(1)(a) protects speech.", pack).ref == "COI Article 19"


def test_nonexistent_article(pack):
    c = only("Article 500 of the Constitution of India", pack)
    assert (c.status, c.severity) == ("nonexistent", "error")


# ── case law ──────────────────────────────────────────────────────────────────
def test_case_with_matching_citation_is_verified(pack):
    c = only("See Maneka Gandhi v. Union of India (1978) 1 SCC 248 on fairness.", pack)
    assert (c.kind, c.status) == ("case", "verified")
    assert c.title == "Maneka Gandhi v. Union of India"


def test_reporter_citation_alone_is_enough_to_verify(pack):
    c = only("The test is in (2014) 8 SCC 273.", pack)
    assert c.status == "verified" and "Arnesh Kumar" in c.title


def test_citation_attached_to_the_wrong_case_is_a_mismatch(pack):
    c = only("Ramesh Kumar v. State of Haryana (1978) 1 SCC 248 settled this.", pack)
    assert (c.status, c.severity) == ("mismatch", "error")
    assert "Maneka Gandhi" in c.message


def test_unknown_reporter_citation_is_unverified(pack):
    c = only("Sharma v. State of Punjab (2019) 4 SCC 123 held otherwise.", pack)
    assert (c.status, c.severity) == ("unverified", "warning")


def test_air_citation_is_matched(pack):
    c = only("Kesavananda Bharati v. State of Kerala, AIR 1973 SC 1461", pack)
    assert c.status == "verified"


def test_case_named_without_a_citation_is_matched_by_name(pack):
    c = only("As in Kesavananda Bharati v. State of Kerala the basic structure is protected.", pack)
    assert c.status == "verified" and c.ref == "(1973) 4 SCC 225"


def test_invented_case_name_is_unverified(pack):
    c = only("In Rajesh Verma v. State of Nowhere the court said so.", pack)
    assert (c.status, c.severity) == ("unverified", "warning")


def test_citation_and_name_are_not_double_counted(pack):
    found = extract_and_verify("Maneka Gandhi v. Union of India (1978) 1 SCC 248", pack)
    assert len(found) == 1


# ── review aggregate ──────────────────────────────────────────────────────────
def test_review_status_levels():
    reviewer = LegalReviewer()
    assert reviewer.review("Section 103 BNS", "India").status == "clean"
    assert reviewer.review("Section 302 IPC", "India").status == "notices"
    assert reviewer.review("Section 9999 BNS", "India").status == "flagged"
    assert reviewer.review("No law cited at all.", "India").status == "clean"


def test_review_without_a_pack_does_not_pretend():
    review = LegalReviewer().review("Section 302 IPC", "Atlantis")
    assert review.status == "no_pack" and review.citations == []


def test_country_alias_and_jurisdiction_fallback():
    reviewer = LegalReviewer()
    assert reviewer.pack_for("INDIA").id == "IN"
    assert reviewer.pack_for("Bharat").id == "IN"
    assert reviewer.pack_for("", "IN").id == "IN"
    assert reviewer.pack_for("France") is None


def test_correction_note_only_for_errors():
    reviewer = LegalReviewer()
    assert correction_note_from(reviewer.review("Section 302 IPC", "India").to_dict()) == ""
    note = correction_note_from(reviewer.review("Section 9999 BNS", "India").to_dict())
    assert "Section 9999 of the BNS" in note or "9999" in note
    assert "Do not repeat" in note
    assert correction_note_from(None) == ""


def test_context_for_returns_relevant_provisions():
    text, refs = LegalReviewer().context_for(
        "electronic evidence certificate 65B WhatsApp chat", "India"
    )
    assert "BSA 63" in refs
    assert "Reference index" in text
    assert "Do not invent" in text  # jurisdiction prompt note travels with the context


def test_context_for_unknown_country_is_empty():
    assert LegalReviewer().context_for("murder", "Atlantis") == ("", [])


# ── pack data integrity ───────────────────────────────────────────────────────
def test_every_concordance_target_exists_in_the_index(pack):
    for old, new in pack.concordance.items():
        act, sec = new.split(" ", 1)
        assert pack.provision(act, sec) is not None, f"{old} -> {new} has no indexed target"


def test_every_replaces_reference_is_in_the_concordance(pack):
    for prov in pack.provisions.values():
        for old in prov.replaces:
            old_act, old_sec = old.split(" ", 1)
            assert pack.successor_of(old_act, old_sec) is not None, f"{prov.ref} replaces {old}"


def test_every_indexed_section_is_within_its_act_range(pack):
    for prov in pack.provisions.values():
        act = pack.acts[prov.act]
        assert int(normalise_section(prov.section).rstrip("ABCDEFGHIJKLMNOPQRSTUVWXYZ")) <= act.max_section


def test_pack_is_marked_as_a_starter_index(pack):
    assert pack.status == "starter_index"
    assert "verify" in pack.notice.lower()


def test_party_name_normalisation():
    assert normalise_party_name("Maneka Gandhi vs. Union of India") == normalise_party_name(
        "Maneka Gandhi v. Union of India"
    )
    assert normalise_party_name("Union of India & Ors.") == "union india"
    assert normalise_section("65b(4)(a)") == "65B"


# ── the matter being argued is not an authority ───────────────────────────────
def test_naming_the_case_on_trial_is_not_a_citation(pack):
    text = "We are convened in the matter of State v. Sample (dev), under Section 103 BNS."
    found = extract_and_verify(text, pack, own_case="State v. Sample (dev)")
    assert [c.ref for c in found] == ["BNS 103"]


def test_other_cases_are_still_checked_when_one_is_on_trial(pack):
    found = extract_and_verify(
        "In State v. Sample the accused pleaded; compare Rajesh Verma v. State of Nowhere.",
        pack, own_case="State v. Sample",
    )
    assert [c.status for c in found] == ["unverified"]
    assert "Rajesh Verma" in found[0].raw


def test_a_reporter_citation_is_still_verified_even_for_the_case_on_trial(pack):
    found = extract_and_verify(
        "Maneka Gandhi v. Union of India (1978) 1 SCC 248", pack, own_case="Maneka Gandhi v. Union of India"
    )
    assert [c.status for c in found] == ["verified"]  # a citation to a reporter is always an authority


def test_without_an_own_case_behaviour_is_unchanged(pack):
    assert len(extract_and_verify("In State v. Sample the court held", pack)) == 1


def test_reviewer_threads_the_case_title_through():
    r = LegalReviewer().review("The matter of State v. Kumar is called.", "India", own_case="State v. Kumar")
    assert r.status == "clean" and r.citations == []


# ── party names are read from the right place ─────────────────────────────────
def test_leading_prose_is_not_part_of_the_case_name(pack):
    found = extract_and_verify(
        "As held in (2014) 8 SCC 273. The defence cites Ramesh Kumar v. State of Haryana (1978) 1 SCC 248"
        " and Rajesh Verma v. State of Nowhere (2019) 4 SCC 123 for the point.", pack)
    raws = {c.status: c.raw for c in found}
    assert raws["mismatch"] == "Ramesh Kumar v. State of Haryana (1978) 1 SCC 248"
    assert raws["unverified"] == "Rajesh Verma v. State of Nowhere (2019) 4 SCC 123"


def test_a_name_wrapped_across_lines_is_tidied(pack):
    found = extract_and_verify(
        "see Arjun Panditrao Khotkar v. Kailash\nKushanrao Gorantyal (2020) 7 SCC 1.", pack)
    assert found[0].status == "verified"
    assert "\n" not in found[0].raw and found[0].raw.startswith("Arjun Panditrao Khotkar v. Kailash Kushanrao")


def test_initials_and_ors_do_not_cut_a_party_name(pack):
    found = extract_and_verify("K.S. Puttaswamy (Retd.) v. Union of India (2017) 10 SCC 1", pack)
    assert found[0].status == "verified"
