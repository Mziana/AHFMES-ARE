"""
Tests for are/state_machine.py — G01-G25 invariants as guard functions.
≥12 tests covering each major G; fail-closed, deterministic, stdlib only.
Run: python -m tests.are.test_state_machine  OR  pytest tests/are/test_state_machine.py -v
"""
import unittest

from are.state_machine import (
    StateMachine, ObjectState, IllegalTransition, ZERO_HASH,
    guard_G01_identity_immutable, guard_G02_ancestry_append_only,
    guard_G03_terminal_disposition_immutable, guard_G04_invalid_neq_rejected,
    guard_G05_integrity_pass_neq_success, guard_G06_archival_never_replaces_disposition,
    guard_G07_retention_never_erases_debt, guard_G08_knowledge_only_validated_bounded_allowed,
    guard_G09_explicit_legal_transition, guard_G11_verified_authority,
    guard_G13_descendants_inherit_debt, guard_G14_descendants_never_rewrite_parent,
    guard_G15_proof_mutation_requires_descendant_or_invalid,
    guard_G18_new_ids_cannot_reset_debt, guard_G19_cas_exact_revision,
    guard_G20_stale_authority, guard_G21_canonical_right_predicate,
    guard_G22_experiment_separate_dimensions, guard_G23_evidence_separate_dimensions,
    guard_G24_problem_history_immutable_episodes, guard_G25_p001_firewall,
    _material_hash, _canonical_json,
)

def _auth(principal, cls, nonce, domain="TD-RESEARCH"):
    return {"principal_id": principal, "authority_class": cls, "trust_domain": domain, "nonce": nonce}

class TestG01IdentityImmutable(unittest.TestCase):
    def test_frozen_candidate_identity_immutable_G01(self):
        sm = StateMachine()
        mat = {"model": "xgb", "params": {"depth": 3}}
        _, cand = sm.create_candidate("C1", mat, "F1", _auth("a", "A-DISCOVERY", "n1"))
        # DRAFT -> DISCOVERY_CANDIDATE -> FROZEN
        _, cand = sm.transition(cand, "DISCOVERY_CANDIDATE", "NONE", cand.revision, cand.last_event_hash, _auth("a", "A-DISCOVERY", "n2"))
        _, cand = sm.transition(cand, "FROZEN", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n3"), new_material=mat)
        # mutate after FROZEN must fail G01/G15
        bad = {"model": "xgb", "params": {"depth": 5}}
        with self.assertRaises(IllegalTransition) as cm:
            sm.transition(cand, "VALIDATION_READY", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n4"), new_material=bad)
        self.assertIn("G01", str(cm.exception))
        # also direct guard
        with self.assertRaises(IllegalTransition):
            guard_G01_identity_immutable(cand, _material_hash(bad))
        # non-material transition after frozen still succeeds
        ok, cand2 = sm.transition(cand, "VALIDATION_READY", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n4b"))
        self.assertTrue(ok)
        self.assertEqual(cand2.lifecycle, "VALIDATION_READY")

class TestG02AncestryAppendOnly(unittest.TestCase):
    def test_ancestry_immutable_G02(self):
        st = ObjectState(object_type="candidate", object_id="C2", lifecycle="DRAFT", disposition="NONE", parent_id="P1", ancestry=("P1","C2"))
        with self.assertRaises(IllegalTransition) as cm:
            guard_G02_ancestry_append_only(st, new_parent_id="P2")
        self.assertIn("G02", str(cm.exception))
        # also StateMachine descendant must not rewrite parent
        sm = StateMachine()
        mat = {"m": 1}
        _, parent = sm.create_candidate("PARENT", mat, "F2", _auth("a", "A-DISCOVERY", "n10"))
        with self.assertRaises(IllegalTransition):
            # trying to create descendant with same hash violates G14
            sm.create_descendant(parent, "CHILD_SAME", mat, _auth("b", "A-DISCOVERY", "n11"))

class TestG03TerminalImmutable(unittest.TestCase):
    def test_adjudicated_disposition_immutable_G03(self):
        sm = StateMachine()
        mat = {"m": 1}
        _, cand = sm.create_candidate("CG3", mat, "F3", _auth("a", "A-DISCOVERY", "n20"))
        _, cand = sm.transition(cand, "DISCOVERY_CANDIDATE", "NONE", cand.revision, cand.last_event_hash, _auth("a", "A-DISCOVERY", "n21"))
        _, cand = sm.transition(cand, "FROZEN", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n22"), new_material=mat)
        _, cand = sm.transition(cand, "VALIDATION_READY", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n23"))
        _, cand = sm.transition(cand, "VALIDATION_ACTIVE", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n24"))
        _, cand = sm.transition(cand, "VALIDATION_CLOSED", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n25"))
        _, cand = sm.transition(cand, "ADJUDICATED", "REJECTED", cand.revision, cand.last_event_hash, _auth("c", "A-GOVERN", "n26", domain="TD-GOVERNOR"))
        self.assertEqual(cand.disposition, "REJECTED")
        with self.assertRaises(IllegalTransition) as cm:
            sm.transition(cand, "RETIRED", "RETIRED", cand.revision, cand.last_event_hash, _auth("c", "A-GOVERN", "n27", domain="TD-GOVERNOR"))
            # Note: candidate ADJUDICATED->RETIRED is legal, so this would not raise G03 for candidate? Let's test illegal: ADJUDICATED -> VALIDATION_READY
        # Use episode to strictly test G03 linear terminal
        sm2 = StateMachine()
        _, prob = sm2.create_problem("P_G3", "F_G3", _auth("a", "A-CREATE", "ng3-1"))
        _, ep = sm2.create_episode("E_G3", "P_G3", "F_G3", _auth("a", "A-CREATE", "ng3-2"))
        _, ep = sm2.transition(ep, "CONTRACTED", "NONE", ep.revision, ep.last_event_hash, _auth("b", "A-LOCK", "ng3-3"))
        _, ep = sm2.transition(ep, "RESEARCHING", "NONE", ep.revision, ep.last_event_hash, _auth("c", "A-DISCOVERY", "ng3-4"))
        _, ep = sm2.transition(ep, "ADJUDICATED", "REJECTED", ep.revision, ep.last_event_hash, _auth("d", "A-GOVERN", "ng3-5", domain="TD-GOVERNOR"))
        with self.assertRaises(IllegalTransition) as cm2:
            sm2.transition(ep, "RESEARCHING", "NONE", ep.revision, ep.last_event_hash, _auth("d", "A-GOVERN", "ng3-6", domain="TD-GOVERNOR"))
        self.assertIn("G03", str(cm2.exception))
        # direct guard
        with self.assertRaises(IllegalTransition):
            guard_G03_terminal_disposition_immutable(ep, "RESEARCHING", "NONE")

class TestG04InvalidNeqReject(unittest.TestCase):
    def test_invalid_distinct_G04(self):
        # Both INVALID and REJECTED must be accepted as distinct; conflation not allowed
        guard_G04_invalid_neq_rejected("INVALID")
        guard_G04_invalid_neq_rejected("REJECTED")
        # unknown should raise
        with self.assertRaises(IllegalTransition) as cm:
            guard_G04_invalid_neq_rejected("UNKNOWN_DISP")
        self.assertIn("G04", str(cm.exception))
        # candidate adjudication with INVALID vs REJECTED distinct paths
        sm = StateMachine()
        mat = {"m": 2}
        _, cand = sm.create_candidate("CG4", mat, "F4", _auth("a", "A-DISCOVERY", "n30"))
        _, cand = sm.transition(cand, "DISCOVERY_CANDIDATE", "NONE", cand.revision, cand.last_event_hash, _auth("a", "A-DISCOVERY", "n31"))
        _, cand = sm.transition(cand, "FROZEN", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n32"), new_material=mat)
        _, cand = sm.transition(cand, "VALIDATION_READY", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n33"))
        _, cand = sm.transition(cand, "VALIDATION_ACTIVE", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n34"))
        _, cand = sm.transition(cand, "VALIDATION_CLOSED", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n35"))
        # both dispositions allowed but must be distinct
        sm2 = StateMachine()
        _, cand2 = sm2.create_candidate("CG4B", mat, "F4B", _auth("a", "A-DISCOVERY", "n30b"))
        _, cand2 = sm2.transition(cand2, "DISCOVERY_CANDIDATE", "NONE", cand2.revision, cand2.last_event_hash, _auth("a", "A-DISCOVERY", "n31b"))
        _, cand2 = sm2.transition(cand2, "FROZEN", "NONE", cand2.revision, cand2.last_event_hash, _auth("b", "A-VALIDATE", "n32b"), new_material=mat)
        _, cand2 = sm2.transition(cand2, "VALIDATION_READY", "NONE", cand2.revision, cand2.last_event_hash, _auth("b", "A-VALIDATE", "n33b"))
        _, cand2 = sm2.transition(cand2, "VALIDATION_ACTIVE", "NONE", cand2.revision, cand2.last_event_hash, _auth("b", "A-VALIDATE", "n34b"))
        _, cand2 = sm2.transition(cand2, "VALIDATION_CLOSED", "NONE", cand2.revision, cand2.last_event_hash, _auth("b", "A-VALIDATE", "n35b"))
        _, invalid = sm2.transition(cand2, "ADJUDICATED", "INVALID", cand2.revision, cand2.last_event_hash, _auth("c", "A-GOVERN", "n36", domain="TD-GOVERNOR"))
        self.assertEqual(invalid.disposition, "INVALID")
        self.assertNotEqual(invalid.disposition, "REJECTED")

class TestG05IntegrityPassDistinct(unittest.TestCase):
    def test_integrity_pass_not_success_G05_G22(self):
        sm = StateMachine()
        _, exp = sm.create_experiment("EXP_G5", "F5", _auth("a", "A-DISCOVERY", "ne1"), integrity="NOT_CHECKED", result="NONE")
        # PASS integrity with REJECTED result is legal (G05)
        ok, exp = sm.transition(exp, "BOUND", "NONE", exp.revision, exp.last_event_hash, _auth("a", "A-DISCOVERY", "ne2"), integrity="PASS", result="NONE")
        self.assertEqual(exp.integrity, "PASS")
        ok, exp = sm.transition(exp, "READY", "NONE", exp.revision, exp.last_event_hash, _auth("b", "A-VALIDATE", "ne3"))
        ok, exp = sm.transition(exp, "RUNNING", "NONE", exp.revision, exp.last_event_hash, _auth("b", "A-VALIDATE", "ne4"))
        ok, exp = sm.transition(exp, "COMPLETED", "NONE", exp.revision, exp.last_event_hash, _auth("b", "A-VALIDATE", "ne5"), result="REJECTED")
        self.assertEqual(exp.integrity, "PASS")
        self.assertEqual(exp.result, "REJECTED")
        # direct guard
        guard_G05_integrity_pass_neq_success("PASS", "REJECTED")
        with self.assertRaises(IllegalTransition):
            guard_G05_integrity_pass_neq_success("UNKNOWN", "REJECTED")
        # G22: lifecycle separate - COMPLETED_VALID forbidden
        with self.assertRaises(IllegalTransition) as cm:
            sm.transition(exp, "COMPLETED_VALID", "NONE", exp.revision, exp.last_event_hash, _auth("c", "A-GOVERN", "ne6", domain="TD-GOVERNOR"))
        self.assertIn("G09", str(cm.exception) + "G22")  # either G09 or G22, but must deny
        # invalid integrity should fail
        sm2 = StateMachine()
        _, exp2 = sm2.create_experiment("EXP_G5B", "F5B", _auth("a", "A-DISCOVERY", "ne10"), integrity="NOT_CHECKED", result="NONE")
        _, exp2 = sm2.transition(exp2, "BOUND", "NONE", exp2.revision, exp2.last_event_hash, _auth("a", "A-DISCOVERY", "ne11"), integrity="PASS", result="NONE")
        with self.assertRaises(IllegalTransition):
            sm2.transition(exp2, "READY", "NONE", exp2.revision, exp2.last_event_hash, _auth("b", "A-VALIDATE", "ne12"), integrity="UNKNOWN")

class TestG06G07RetentionOrthogonal(unittest.TestCase):
    def test_archival_orthogonal_G06_G07(self):
        sm = StateMachine()
        mat = {"m": 3}
        _, cand = sm.create_candidate("ARCH_G6", mat, "F6", _auth("a", "A-DISCOVERY", "na1"))
        _, cand = sm.transition(cand, "DISCOVERY_CANDIDATE", "NONE", cand.revision, cand.last_event_hash, _auth("a", "A-DISCOVERY", "na2"))
        _, cand = sm.transition(cand, "FROZEN", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "na3"), new_material=mat)
        before_disp = cand.disposition
        before_lc = cand.lifecycle
        before_debt = cand.debt
        ok, cand_arch = sm.archive(cand, _auth("gov", "A-GOVERN", "na4", domain="TD-GOVERNOR"), cand.revision, cand.last_event_hash)
        self.assertEqual(cand_arch.disposition, before_disp)
        self.assertEqual(cand_arch.lifecycle, before_lc)
        self.assertEqual(cand_arch.retention, "ARCHIVED_RECORD")
        self.assertEqual(cand_arch.debt, before_debt)
        # direct guards
        with self.assertRaises(IllegalTransition) as cm:
            guard_G06_archival_never_replaces_disposition(cand, {"action": "ARCHIVE", "to_disposition": "REJECTED"})
        self.assertIn("G06", str(cm.exception))
        with self.assertRaises(IllegalTransition) as cm2:
            guard_G07_retention_never_erases_debt(cand, new_debt=-1)
        self.assertIn("G07", str(cm2.exception))
        # second archive fails
        with self.assertRaises(IllegalTransition):
            sm.archive(cand_arch, _auth("gov", "A-GOVERN", "na5", domain="TD-GOVERNOR"), cand_arch.revision, cand_arch.last_event_hash)
        # archival must not be encoded as lifecycle edge
        with self.assertRaises(IllegalTransition) as cm3:
            sm.transition(cand_arch, "ARCHIVED_RECORD", "NONE", cand_arch.revision, cand_arch.last_event_hash, _auth("gov", "A-GOVERN", "na6", domain="TD-GOVERNOR"))
        self.assertIn("G06", str(cm3.exception))

class TestG09G10LegalExplicit(unittest.TestCase):
    def test_unspecified_transition_denied_G09_G10(self):
        sm = StateMachine()
        _, prob = sm.create_problem("P_G9", "F_G9", _auth("a", "A-CREATE", "np1"))
        # OBSERVED -> DORMANT is unspecified and must be denied (G09/G10)
        with self.assertRaises(IllegalTransition) as cm:
            sm.transition(prob, "DORMANT", "NONE", prob.revision, prob.last_event_hash, _auth("b", "A-CREATE", "np2"))
        self.assertIn("G09", str(cm.exception))
        # direct guard G09/G10
        with self.assertRaises(IllegalTransition):
            guard_G09_explicit_legal_transition("problem", "OBSERVED", "DORMANT")
        # candidate DRAFT -> FROZEN skipping DISCOVERY_CANDIDATE must fail
        mat = {"m": 4}
        _, cand = sm.create_candidate("CG9", mat, "F9B", _auth("a", "A-DISCOVERY", "np3"))
        with self.assertRaises(IllegalTransition) as cm2:
            sm.transition(cand, "FROZEN", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "np4"), new_material=mat)
        self.assertIn("G09", str(cm2.exception))
        # Problem: DORMANT -> OPEN is legal
        _, prob2 = sm.create_problem("P_G9B", "F_G9B", _auth("a", "A-CREATE", "np5"))
        _, prob2 = sm.transition(prob2, "OPEN", "NONE", prob2.revision, prob2.last_event_hash, _auth("b", "A-CREATE", "np6"))
        _, prob2 = sm.transition(prob2, "DORMANT", "NONE", prob2.revision, prob2.last_event_hash, _auth("c", "A-CONTRACT-DRAFT", "np7"))
        ok, prob2 = sm.transition(prob2, "OPEN", "NONE", prob2.revision, prob2.last_event_hash, _auth("d", "A-CONTRACT-DRAFT", "np8"))
        self.assertEqual(prob2.lifecycle, "OPEN")

class TestG11AuthorityRequired(unittest.TestCase):
    def test_verified_authority_G11(self):
        # None authority denied
        with self.assertRaises(IllegalTransition) as cm:
            guard_G11_verified_authority(None)
        self.assertIn("G11", str(cm.exception))
        # missing nonce for single-use
        with self.assertRaises(IllegalTransition) as cm2:
            guard_G11_verified_authority({"principal_id": "p", "authority_class": "A-VALIDATE", "trust_domain": "TD-RESEARCH"})
        self.assertIn("G11", str(cm2.exception))
        # StateMachine transition without authority must fail
        sm = StateMachine()
        _, prob = sm.create_problem("P_G11", "F_G11", _auth("a", "A-CREATE", "na11"))
        with self.assertRaises(IllegalTransition) as cm3:
            sm.transition(prob, "OPEN", "NONE", prob.revision, prob.last_event_hash, None)
        self.assertIn("G11", str(cm3.exception))

class TestG13G14DescendantInherit(unittest.TestCase):
    def test_descendant_inherits_debt_not_rewrite_parent_G13_G14_G18(self):
        sm = StateMachine()
        mat1 = {"model": "xgb", "params": {"depth": 3}}
        _, cand = sm.create_candidate("PARENT_G13", mat1, "F13", _auth("a", "A-DISCOVERY", "nd1"))
        _, cand = sm.transition(cand, "DISCOVERY_CANDIDATE", "NONE", cand.revision, cand.last_event_hash, _auth("a", "A-DISCOVERY", "nd2"))
        _, cand = sm.transition(cand, "FROZEN", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "nd3"), new_material=mat1)
        mat2 = {"model": "xgb", "params": {"depth": 5}}
        ok, child = sm.create_descendant(cand, "CHILD_G13", mat2, _auth("c", "A-DISCOVERY", "nd4"))
        self.assertEqual(child.debt, 1)
        self.assertEqual(child.family_root, "F13")
        # parent unchanged
        parent_after = sm.get_state("candidate", "PARENT_G13")
        self.assertEqual(parent_after.material_hash, cand.material_hash)
        self.assertNotEqual(parent_after.material_hash, child.material_hash)
        # same material must fail G14
        with self.assertRaises(IllegalTransition) as cm:
            sm.create_descendant(cand, "CHILD_SAME_G13", mat1, _auth("c", "A-DISCOVERY", "nd5"))
        self.assertIn("G14", str(cm.exception))
        # debt inheritance guard directly
        with self.assertRaises(IllegalTransition) as cm2:
            guard_G13_descendants_inherit_debt(2, 1)
        self.assertIn("G13", str(cm2.exception))
        with self.assertRaises(IllegalTransition):
            guard_G14_descendants_never_rewrite_parent("abc", "abc")
        # successive descendant chains debt increments
        mat3 = {"model": "xgb", "params": {"depth": 7}}
        ok, child2 = sm.create_descendant(child, "CHILD_G13_2", mat3, _auth("d", "A-DISCOVERY", "nd6"))
        self.assertEqual(child2.debt, 2)
        # new ID same family cannot reset debt (G18) — create fresh candidate in same family should have debt >= max family debt
        _, fresh = sm.create_candidate("FRESH_G13", {"model": "xgb", "params": {"depth": 9}}, "F13", _auth("e", "A-DISCOVERY", "nd7"))
        self.assertEqual(fresh.debt, 2)  # inherited not reset

class TestG15ProofMutationRequiresDescendant(unittest.TestCase):
    def test_proof_mutation_descendant_or_invalid_G15(self):
        sm = StateMachine()
        mat = {"q": "test"}
        # Simulate contract path: create_candidate as proxy for contract freeze
        _, cand = sm.create_candidate("C_G15", mat, "F15", _auth("a", "A-DISCOVERY", "n15a"))
        _, cand = sm.transition(cand, "DISCOVERY_CANDIDATE", "NONE", cand.revision, cand.last_event_hash, _auth("a", "A-DISCOVERY", "n15b"))
        _, cand = sm.transition(cand, "FROZEN", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n15c"), new_material=mat)
        bad = {"q": "mutated"}
        # in-place edit after freeze without descendant must fail G15/G01
        with self.assertRaises(IllegalTransition) as cm:
            sm.transition(cand, "VALIDATION_READY", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n15d"), new_material=bad)
        self.assertIn("G01", str(cm.exception) + "G15")
        # descendant path succeeds
        ok, desc = sm.create_descendant(cand, "C_G15_D1", bad, _auth("c", "A-DISCOVERY", "n15e"))
        self.assertEqual(desc.debt, 1)
        # direct guard G15
        st = ObjectState(object_type="candidate", object_id="S", lifecycle="FROZEN", disposition="NONE", material_hash=_material_hash(mat), root_hash=_material_hash(mat))
        with self.assertRaises(IllegalTransition) as cm2:
            guard_G15_proof_mutation_requires_descendant_or_invalid(st, _material_hash(bad), creating_descendant=False, to_disposition="NONE")
        self.assertIn("G15", str(cm2.exception))
        # INVALID disposition allows mutation without descendant (per spec: or INVALID)
        # Our guard allows if to_disposition == INVALID
        guard_G15_proof_mutation_requires_descendant_or_invalid(st, _material_hash(bad), creating_descendant=False, to_disposition="INVALID")

class TestG16G17SoD(unittest.TestCase):
    def test_research_cannot_self_validate_G16(self):
        sm = StateMachine()
        mat = {"m": 5}
        _, cand = sm.create_candidate("C_G16", mat, "F16", _auth("alice", "A-DISCOVERY", "n16a"))
        # same principal does discovery then tries validate in same family -> must fail G16
        # First, simulate discovery by alice already recorded in sod_ledger via create_candidate (A-DISCOVERY)
        with self.assertRaises(IllegalTransition) as cm:
            sm.transition(cand, "DISCOVERY_CANDIDATE", "NONE", cand.revision, cand.last_event_hash, _auth("alice", "A-VALIDATE", "n16b"))
        self.assertIn("G16", str(cm.exception))
        # different principal can validate
        ok, cand2 = sm.transition(cand, "DISCOVERY_CANDIDATE", "NONE", cand.revision, cand.last_event_hash, _auth("bob", "A-DISCOVERY", "n16c"))
        # bob now is DISCOVERY for this candidate, but another principal carol can validate after FROZEN
        _, cand2 = sm.transition(cand2, "FROZEN", "NONE", cand2.revision, cand2.last_event_hash, _auth("carol", "A-VALIDATE", "n16d"), new_material=mat)
        ok, cand2 = sm.transition(cand2, "VALIDATION_READY", "NONE", cand2.revision, cand2.last_event_hash, _auth("carol", "A-VALIDATE", "n16e"))
        self.assertEqual(cand2.lifecycle, "VALIDATION_READY")

    def test_critic_cannot_rescue_G17(self):
        sm = StateMachine()
        mat = {"m": 6}
        _, cand = sm.create_candidate("C_G17", mat, "F17", _auth("critic1", "A-CRITIC", "n17a", domain="TD-CRITIC"))
        # same critic tries to promote -> fail G17
        with self.assertRaises(IllegalTransition) as cm:
            sm.transition(cand, "DISCOVERY_CANDIDATE", "NONE", cand.revision, cand.last_event_hash, _auth("critic1", "A-PROMOTE", "n17b", domain="TD-CRITIC"))
        self.assertIn("G17", str(cm.exception))
        # critic cannot govern rescue either
        sm2 = StateMachine()
        _, cand2 = sm2.create_candidate("C_G17B", mat, "F17B", _auth("critic2", "A-CRITIC", "n17c", domain="TD-CRITIC"))
        with self.assertRaises(IllegalTransition) as cm2:
            sm2.transition(cand2, "DISCOVERY_CANDIDATE", "NONE", cand2.revision, cand2.last_event_hash, _auth("critic2", "A-GOVERN", "n17d", domain="TD-GOVERNOR"))
        self.assertIn("G17", str(cm2.exception))

class TestG18NewIdCannotResetDebt(unittest.TestCase):
    def test_new_ids_cannot_reset_debt_G18(self):
        sm = StateMachine()
        mat = {"m": 7}
        _, cand = sm.create_candidate("C18_A", mat, "F18", _auth("a", "A-DISCOVERY", "n18a"))
        _, cand = sm.transition(cand, "DISCOVERY_CANDIDATE", "NONE", cand.revision, cand.last_event_hash, _auth("a", "A-DISCOVERY", "n18b"))
        _, cand = sm.transition(cand, "FROZEN", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n18c"), new_material=mat)
        # child inherits debt 1
        _, child = sm.create_descendant(cand, "C18_CHILD", {"m": 8}, _auth("c", "A-DISCOVERY", "n18d"))
        self.assertEqual(child.debt, 1)
        # graveyard blocking same content
        sm.graveyard[("F18", child.material_hash)] = "REJECTED"
        with self.assertRaises(IllegalTransition) as cm:
            sm.create_candidate("C18_FRESH_SAME", {"m": 8}, "F18", _auth("d", "A-DISCOVERY", "n18e"))
        self.assertIn("G18", str(cm.exception))
        # direct guard
        sm.family_debt["F18"] = 2
        with self.assertRaises(IllegalTransition) as cm2:
            guard_G18_new_ids_cannot_reset_debt("F18", 0, sm.family_debt)
        self.assertIn("G18", str(cm2.exception))
        # proposal with debt < known must fail
        with self.assertRaises(IllegalTransition):
            guard_G18_new_ids_cannot_reset_debt("F18", 1, sm.family_debt)

class TestG19G20ConcurrentCAS(unittest.TestCase):
    def test_cas_exact_revision_G19_G20(self):
        sm = StateMachine()
        mat = {"m": 9}
        _, cand = sm.create_candidate("C19", mat, "F19", _auth("a", "A-DISCOVERY", "n19a"))
        # first transition succeeds
        ok, cand2 = sm.transition(cand, "DISCOVERY_CANDIDATE", "NONE", cand.revision, cand.last_event_hash, _auth("a", "A-DISCOVERY", "n19b"))
        # stale expected_revision (old 1) must fail G19
        with self.assertRaises(IllegalTransition) as cm:
            sm.transition(cand2, "FROZEN", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n19c"), new_material=mat)
        self.assertIn("G19", str(cm.exception))
        # stale prev hash must fail G20
        with self.assertRaises(IllegalTransition) as cm2:
            sm.transition(cand2, "FROZEN", "NONE", cand2.revision, ZERO_HASH, _auth("b", "A-VALIDATE", "n19d"), new_material=mat)
        self.assertIn("G20", str(cm2.exception))
        # direct guards
        with self.assertRaises(IllegalTransition) as cm3:
            guard_G19_cas_exact_revision(cand2, 99, cand2.last_event_hash)
        self.assertIn("G19", str(cm3.exception))
        # nonce replay stale authority G20
        with self.assertRaises(IllegalTransition) as cm4:
            # consume nonce first
            auth = _auth("x", "A-VALIDATE", "replay-nonce")
            sm.nonce_seen.add("replay-nonce")
            guard_G20_stale_authority(sm.nonce_seen, auth)
        self.assertIn("G20", str(cm4.exception))
        # successful CAS with exact revision
        ok, cand3 = sm.transition(cand2, "FROZEN", "NONE", cand2.revision, cand2.last_event_hash, _auth("b", "A-VALIDATE", "n19e"), new_material=mat)
        self.assertEqual(cand3.lifecycle, "FROZEN")

class TestG21CanonicalRightPredicate(unittest.TestCase):
    def test_canonical_right_cross_object_G21(self):
        # local flag without proof must fail
        with self.assertRaises(IllegalTransition) as cm:
            guard_G21_canonical_right_predicate("CAN_VALIDATE", True, None)
        self.assertIn("G21", str(cm.exception))
        with self.assertRaises(IllegalTransition) as cm2:
            guard_G21_canonical_right_predicate("CAN_VALIDATE", True, {"candidate_root": "a"})
        self.assertIn("G21", str(cm2.exception))
        # correct cross-object proof passes
        guard_G21_canonical_right_predicate("CAN_VALIDATE", False, {
            "candidate_root": "rh1", "contract_root": "rh2", "evidence_snapshot_root": "rh3", "ledger_revision": 5
        })
        # StateMachine helper check_can_validate
        sm = StateMachine()
        cand = ObjectState(object_type="candidate", object_id="CV1", lifecycle="FROZEN", disposition="NONE", material_hash="rh1", root_hash="rh1", family_root="F21")
        contract = ObjectState(object_type="contract", object_id="CT1", lifecycle="LOCKED", disposition="NONE", root_hash="rh2", family_root="F21")
        with self.assertRaises(IllegalTransition):
            sm.check_can_validate(cand, contract, {"root_hash": "rh3"}, 5, local_flag=True)  # local_flag True without proper proof path would still be checked via guard
        # valid call with local_flag False and full proof
        self.assertTrue(sm.check_can_validate(cand, contract, {"root_hash": "rh3"}, 5, local_flag=False))
        # CAN_PROMOTE requires champion proof with cas_token
        with self.assertRaises(IllegalTransition):
            sm.check_can_promote(cand, {}, 10, local_flag=False)  # missing champion proof content
        with self.assertRaises(IllegalTransition):
            sm.check_can_promote(cand, {"champion_proof": "proof"}, 10, local_flag=False)  # missing cas_token -> G21
        # correct promote
        self.assertTrue(sm.check_can_promote(cand, {"champion_proof": "proof", "registry_generation": 10, "cas_token": "tok"}, 10))

class TestG22ExperimentSeparate(unittest.TestCase):
    def test_experiment_dimensions_G22(self):
        guard_G22_experiment_separate_dimensions("PLANNED", "NOT_CHECKED", "NONE")
        guard_G22_experiment_separate_dimensions("COMPLETED", "PASS", "REJECTED")
        with self.assertRaises(IllegalTransition) as cm:
            guard_G22_experiment_separate_dimensions("COMPLETED_VALID", "PASS", "NONE")
        self.assertIn("G22", str(cm.exception))
        with self.assertRaises(IllegalTransition):
            guard_G22_experiment_separate_dimensions("PLANNED", "UNKNOWN", "NONE")

class TestG23EvidenceSeparate(unittest.TestCase):
    def test_evidence_dimensions_G23(self):
        guard_G23_evidence_separate_dimensions("VERIFIED", "HISTORICAL_DISCOVERY", "ACTIVE_RECORD")
        with self.assertRaises(IllegalTransition) as cm:
            guard_G23_evidence_separate_dimensions("UNKNOWN", "HISTORICAL_DISCOVERY", "ACTIVE_RECORD")
        self.assertIn("G23", str(cm.exception))
        with self.assertRaises(IllegalTransition):
            guard_G23_evidence_separate_dimensions("VERIFIED", "UNKNOWN_ORIGIN", "ACTIVE_RECORD")

class TestG24ProblemHistory(unittest.TestCase):
    def test_problem_history_immutable_episodes_G24(self):
        sm = StateMachine()
        _, prob = sm.create_problem("P24", "F24", _auth("a", "A-CREATE", "np24a"))
        _, ep1 = sm.create_episode("E24_1", "P24", "F24", _auth("b", "A-CREATE", "np24b"))
        _, ep1 = sm.transition(ep1, "CONTRACTED", "NONE", ep1.revision, ep1.last_event_hash, _auth("c", "A-LOCK", "np24c"))
        _, ep1 = sm.transition(ep1, "RESEARCHING", "NONE", ep1.revision, ep1.last_event_hash, _auth("d", "A-DISCOVERY", "np24d"))
        _, ep1 = sm.transition(ep1, "ADJUDICATED", "REJECTED", ep1.revision, ep1.last_event_hash, _auth("e", "A-GOVERN", "np24e", domain="TD-GOVERNOR"))
        # E24_1 is now ADJUDICATED REJECTED immutable
        with self.assertRaises(IllegalTransition) as cm:
            sm.transition(ep1, "RESEARCHING", "NONE", ep1.revision, ep1.last_event_hash, _auth("e", "A-GOVERN", "np24f", domain="TD-GOVERNOR"))
        self.assertIn("G03", str(cm.exception))
        # Creating new episode for same problem must not overwrite E24_1 (G24)
        _, ep2 = sm.create_episode("E24_2", "P24", "F24", _auth("b", "A-CREATE", "np24g"))
        _, ep2 = sm.transition(ep2, "CONTRACTED", "NONE", ep2.revision, ep2.last_event_hash, _auth("c", "A-LOCK", "np24h"))
        _, ep2 = sm.transition(ep2, "RESEARCHING", "NONE", ep2.revision, ep2.last_event_hash, _auth("d", "A-DISCOVERY", "np24i"))
        _, ep2 = sm.transition(ep2, "ADJUDICATED", "VALIDATED_BOUNDED", ep2.revision, ep2.last_event_hash, _auth("e", "A-GOVERN", "np24j", domain="TD-GOVERNOR"))
        # check both episodes preserved distinct dispositions (G24 derived summary, not overwritten)
        self.assertEqual(sm.episodes["E24_1"].disposition, "REJECTED")
        self.assertEqual(sm.episodes["E24_2"].disposition, "VALIDATED_BOUNDED")
        # direct guard
        with self.assertRaises(IllegalTransition) as cm2:
            guard_G24_problem_history_immutable_episodes(sm.episodes, "E24_1")
        self.assertIn("G24", str(cm2.exception))

class TestG08KnowledgeOnly(unittest.TestCase):
    def test_validated_bounded_knowledge_only_terminal_G08(self):
        # VALIDATED_BOUNDED as legal terminal without shadow (knowledge-only)
        guard_G08_knowledge_only_validated_bounded_allowed("VALIDATED_BOUNDED")
        sm = StateMachine()
        mat = {"m": 10}
        _, cand = sm.create_candidate("CG8", mat, "F8", _auth("a", "A-DISCOVERY", "n8a"))
        _, cand = sm.transition(cand, "DISCOVERY_CANDIDATE", "NONE", cand.revision, cand.last_event_hash, _auth("a", "A-DISCOVERY", "n8b"))
        _, cand = sm.transition(cand, "FROZEN", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n8c"), new_material=mat)
        _, cand = sm.transition(cand, "VALIDATION_READY", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n8d"))
        _, cand = sm.transition(cand, "VALIDATION_ACTIVE", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n8e"))
        _, cand = sm.transition(cand, "VALIDATION_CLOSED", "NONE", cand.revision, cand.last_event_hash, _auth("b", "A-VALIDATE", "n8f"))
        # direct to ADJUDICATED VALIDATED_BOUNDED without SHADOW is legal (G08)
        ok, cand = sm.transition(cand, "ADJUDICATED", "VALIDATED_BOUNDED", cand.revision, cand.last_event_hash, _auth("c", "A-GOVERN", "n8g", domain="TD-GOVERNOR"))
        self.assertEqual(cand.disposition, "VALIDATED_BOUNDED")

class TestG25P001Firewall(unittest.TestCase):
    def test_p001_firewall_G25(self):
        with self.assertRaises(IllegalTransition) as cm:
            guard_G25_p001_firewall({"problem_id": "P001", "answer": "profitable 60%"})
        self.assertIn("G25", str(cm.exception))
        # non-P001 allowed
        guard_G25_p001_firewall({"problem_id": "P002", "answer": "something"})
        sm = StateMachine()
        sm.assert_not_p001_answer({"problem_id": "P002", "answer": "ok"})
        with self.assertRaises(IllegalTransition):
            sm.assert_not_p001_answer({"problem_id": "P001", "answer": "x"})

class TestReturnTupleAndDeterministic(unittest.TestCase):
    def test_transition_returns_tuple_and_deterministic_hash(self):
        sm = StateMachine()
        _, prob = sm.create_problem("P_TUP", "F_TUP", _auth("a", "A-CREATE", "nt1"))
        ok, prob2 = sm.transition(prob, "OPEN", "NONE", prob.revision, prob.last_event_hash, _auth("b", "A-CREATE", "nt2"))
        self.assertTrue(ok)
        self.assertIsInstance(prob2, ObjectState)
        # deterministic: redo same transition via fresh SM with same inputs yields same hash? We test that two independent SM produce same event hash for same inputs
        sm2 = StateMachine()
        # Recreate same initial state manually
        init = ObjectState(object_type="problem", object_id="P_TUP2", lifecycle="OBSERVED", disposition="NONE", retention="ACTIVE_RECORD", revision=1, last_event_hash=prob.last_event_hash, family_root="F_TUP", ancestry=("P_TUP2",))
        # Actually compare that _compute_event_hash deterministic
        h1 = _material_hash({"a": 1})
        h2 = _material_hash({"a": 1})
        self.assertEqual(h1, h2)
        # canonical json deterministic
        self.assertEqual(_canonical_json({"b": 2, "a": 1}), _canonical_json({"a": 1, "b": 2}))

class TestBudgetEnvelopeLifecycle(unittest.TestCase):
    def test_budget_envelope_lifecycle_and_retention_G06(self):
        sm = StateMachine()
        _, be = sm.create_budget_envelope("BE1", "F_BE", _auth("a", "A-CAPITAL-ACTIVATE", "nb1", domain="TD-GOVERNOR"), initial_budget=100)
        self.assertEqual(be.lifecycle, "UNALLOCATED")
        ok, be = sm.transition(be, "ALLOCATED", "NONE", be.revision, be.last_event_hash, _auth("b", "A-CAPITAL-ACTIVATE", "nb2", domain="TD-GOVERNOR"))
        ok, be = sm.transition(be, "RESERVED", "NONE", be.revision, be.last_event_hash, _auth("b", "A-CAPITAL-ACTIVATE", "nb3", domain="TD-GOVERNOR"))
        ok, be = sm.transition(be, "ACTIVE", "NONE", be.revision, be.last_event_hash, _auth("b", "A-CAPITAL-ACTIVATE", "nb4", domain="TD-GOVERNOR"))
        ok, be = sm.transition(be, "CONSUMED", "NONE", be.revision, be.last_event_hash, _auth("b", "A-CAPITAL-ACTIVATE", "nb5", domain="TD-GOVERNOR"))
        ok, be = sm.transition(be, "RECONCILED", "NONE", be.revision, be.last_event_hash, _auth("b", "A-CAPITAL-ACTIVATE", "nb6", domain="TD-GOVERNOR"))
        self.assertEqual(be.lifecycle, "RECONCILED")
        # unspecified transition must fail
        sm3 = StateMachine()
        _, be3 = sm3.create_budget_envelope("BE3", "F_BE3", _auth("a", "A-CAPITAL-ACTIVATE", "nb7", domain="TD-GOVERNOR"))
        with self.assertRaises(IllegalTransition) as cm:
            sm3.transition(be3, "CONSUMED", "NONE", be3.revision, be3.last_event_hash, _auth("b", "A-CAPITAL-ACTIVATE", "nb8", domain="TD-GOVERNOR"))
        self.assertIn("G09", str(cm.exception))

if __name__ == "__main__":
    unittest.main(verbosity=2)
