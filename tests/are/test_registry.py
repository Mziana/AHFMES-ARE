"""
Tests for are/registry.py — Scientific Registry G01-G25
Minimal 15+ tests: lifecycle, CAS, immutable disposition, retry descendant rules
Run: python -m tests.are.test_registry  OR python -m pytest tests/are/test_registry.py -v
"""
import gc
import os
import tempfile
import time
import unittest
import hashlib

from are.registry import Registry, RegistryError
from are.storage import EventStore

def _tmp_db():
    td = tempfile.mkdtemp()
    p = os.path.join(td, "reg.db")
    return p, td

def _clean(p, td):
    gc.collect()
    for suffix in ["", "-wal","-shm"]:
        fp = p+suffix
        for _ in range(5):
            try:
                if os.path.exists(fp):
                    os.unlink(fp)
                break
            except PermissionError:
                gc.collect()
                time.sleep(0.05)
    try:
        os.rmdir(td)
    except: pass

def _auth(principal, cls, nonce, domain="TD-RESEARCH"):
    return {"principal_id": principal, "authority_class": cls, "trust_domain": domain, "nonce": nonce}

class TestProblemLifecycle(unittest.TestCase):
    def setUp(self):
        self.db, self.td = _tmp_db()
        self.reg = Registry(self.db)
    def tearDown(self):
        self.reg.close()
        _clean(self.db, self.td)

    def test_problem_lifecycle_valid(self):
        a1 = _auth("alice","A-CREATE","n1")
        r = self.reg.create_problem("P100","statement A", a1, family_root="F100")
        self.assertEqual(r["lifecycle"],"OBSERVED")
        # OBSERVED->OPEN
        a2 = _auth("bob","A-CREATE","n2")
        t = self.reg.transition_problem("P100","OPEN", a2, r["revision"], r["last_event_hash"])
        self.assertEqual(t["lifecycle"],"OPEN")
        # OPEN->DORMANT
        a3 = _auth("carol","A-CONTRACT-DRAFT","n3")
        t2 = self.reg.transition_problem("P100","DORMANT", a3, t["revision"], t["last_event_hash"])
        self.assertEqual(t2["lifecycle"],"DORMANT")
        # DORMANT->OPEN
        a4 = _auth("dave","A-CONTRACT-DRAFT","n4")
        t3 = self.reg.transition_problem("P100","OPEN", a4, t2["revision"], t2["last_event_hash"])
        self.assertEqual(t3["lifecycle"],"OPEN")
        # OPEN->RETIRED
        a5 = _auth("gov","A-GOVERN","n5","TD-GOVERNOR")
        t4 = self.reg.transition_problem("P100","RETIRED", a5, t3["revision"], t3["last_event_hash"])
        self.assertEqual(t4["lifecycle"],"RETIRED")

    def test_problem_invalid_transition_denied(self):
        a1 = _auth("alice","A-CREATE","n10")
        r = self.reg.create_problem("P101","stmt", a1)
        # OBSERVED->DORMANT is illegal (must go via OPEN)
        a2 = _auth("bob","A-CREATE","n11")
        with self.assertRaises(RegistryError) as cm:
            self.reg.transition_problem("P101","DORMANT", a2, r["revision"], r["last_event_hash"])
        self.assertIn("G09", str(cm.exception))

    def test_problem_requires_authority(self):
        with self.assertRaises(RegistryError) as cm:
            self.reg.create_problem("P102","stmt", None)
        self.assertIn("G11", str(cm.exception))

    def test_problem_chain_verified(self):
        a1 = _auth("alice","A-CREATE","n20")
        r = self.reg.create_problem("P103","stmt", a1)
        a2 = _auth("bob","A-CREATE","n21")
        self.reg.transition_problem("P103","OPEN", a2, r["revision"], r["last_event_hash"])
        self.assertTrue(self.reg.verify_chain("problem","P103"))

class TestEpisodeImmutable(unittest.TestCase):
    def setUp(self):
        self.db, self.td = _tmp_db()
        self.reg = Registry(self.db)
        self.a_prob = _auth("alice","A-CREATE","ep-n1")
        self.pr = self.reg.create_problem("P200","stmt", self.a_prob, family_root="F200")
        # open problem for episode creation
        self.reg.transition_problem("P200","OPEN", _auth("bob","A-CREATE","ep-n2"), self.pr["revision"], self.pr["last_event_hash"])
    def tearDown(self):
        self.reg.close()
        _clean(self.db, self.td)

    def test_episode_lifecycle_linear_and_immutable_disposition(self):
        ep = self.reg.create_episode("E1","P200", _auth("carol","A-CONTRACT-DRAFT","ep-n3"))
        self.assertEqual(ep["lifecycle"],"PLANNED")
        # PLANNED->CONTRACTED
        t1 = self.reg.transition_episode("E1","CONTRACTED","NONE", _auth("carol","A-LOCK","ep-n4"), ep["revision"], ep["last_event_hash"])
        self.assertEqual(t1["lifecycle"],"CONTRACTED")
        # CONTRACTED->RESEARCHING
        t2 = self.reg.transition_episode("E1","RESEARCHING","NONE", _auth("dave","A-DISCOVERY","ep-n5"), t1["revision"], t1["last_event_hash"])
        # RESEARCHING->ADJUDICATED with REJECTED
        t3 = self.reg.transition_episode("E1","ADJUDICATED","REJECTED", _auth("eve","A-GOVERN","ep-n6","TD-GOVERNOR"), t2["revision"], t2["last_event_hash"])
        self.assertEqual(t3["disposition"],"REJECTED")
        # Attempt to change disposition after ADJUDICATED -> G03 fail
        with self.assertRaises(RegistryError) as cm:
            self.reg.transition_episode("E1","ADJUDICATED","VALIDATED_BOUNDED", _auth("eve","A-GOVERN","ep-n7","TD-GOVERNOR"), t3["revision"], t3["last_event_hash"])
        self.assertIn("G03", str(cm.exception))
        # Also any further lifecycle change denied
        with self.assertRaises(RegistryError):
            self.reg.transition_episode("E1","RESEARCHING","NONE", _auth("eve","A-GOVERN","ep-n8","TD-GOVERNOR"), t3["revision"], t3["last_event_hash"])

    def test_episode_history_not_overwritten_G24(self):
        ep1 = self.reg.create_episode("E2","P200", _auth("alice","A-CREATE","ep2-n1"))
        t1 = self.reg.transition_episode("E2","CONTRACTED","NONE", _auth("b","A-LOCK","ep2-n2"), ep1["revision"], ep1["last_event_hash"])
        t2 = self.reg.transition_episode("E2","RESEARCHING","NONE", _auth("c","A-DISCOVERY","ep2-n3"), t1["revision"], t1["last_event_hash"])
        t3 = self.reg.transition_episode("E2","ADJUDICATED","REJECTED", _auth("d","A-GOVERN","ep2-n4","TD-GOVERNOR"), t2["revision"], t2["last_event_hash"])
        # New episode for same problem preserves old disposition (G24)
        ep2 = self.reg.create_episode("E3","P200", _auth("alice","A-CREATE","ep2-n5"))
        t4 = self.reg.transition_episode("E3","CONTRACTED","NONE", _auth("b","A-LOCK","ep2-n6"), ep2["revision"], ep2["last_event_hash"])
        t5 = self.reg.transition_episode("E3","RESEARCHING","NONE", _auth("c","A-DISCOVERY","ep2-n7"), t4["revision"], t4["last_event_hash"])
        t6 = self.reg.transition_episode("E3","ADJUDICATED","VALIDATED_BOUNDED", _auth("d","A-GOVERN","ep2-n8","TD-GOVERNOR"), t5["revision"], t5["last_event_hash"])
        # E2 still REJECTED, not overwritten by E3
        e2 = self.reg.get_episode("E2")
        e3 = self.reg.get_episode("E3")
        self.assertEqual(e2["disposition"],"REJECTED")
        self.assertEqual(e3["disposition"],"VALIDATED_BOUNDED")

    def test_episode_requires_linear(self):
        ep = self.reg.create_episode("E4","P200", _auth("x","A-CREATE","ep3-n1"))
        # PLANNED -> RESEARCHING skipping CONTRACTED should fail
        with self.assertRaises(RegistryError):
            self.reg.transition_episode("E4","RESEARCHING","NONE", _auth("y","A-LOCK","ep3-n2"), ep["revision"], ep["last_event_hash"])

class TestHypothesisAndContract(unittest.TestCase):
    def setUp(self):
        self.db, self.td = _tmp_db()
        self.reg = Registry(self.db)
        self.pr = self.reg.create_problem("P300","stmt", _auth("a","A-CREATE","h-n1"), family_root="F300")
        self.reg.transition_problem("P300","OPEN", _auth("b","A-CREATE","h-n2"), self.pr["revision"], self.pr["last_event_hash"])
        self.ep = self.reg.create_episode("E300","P300", _auth("c","A-CREATE","h-n3"))
    def tearDown(self):
        self.reg.close()
        _clean(self.db, self.td)

    def test_hypothesis_no_reverse(self):
        h = self.reg.create_hypothesis("H1","E300", _auth("d","A-DISCOVERY","h-n4"))
        t1 = self.reg.transition_hypothesis("H1","CONTRACTED","NONE", _auth("e","A-CONTRACT-DRAFT","h-n5"), h["revision"], h["last_event_hash"])
        t2 = self.reg.transition_hypothesis("H1","DISCOVERY_ACTIVE","NONE", _auth("e","A-DISCOVERY","h-n6"), t1["revision"], t1["last_event_hash"])
        # try reverse DISCOVERY_ACTIVE -> CONTRACTED should fail
        with self.assertRaises(RegistryError) as cm:
            self.reg.transition_hypothesis("H1","CONTRACTED","NONE", _auth("e","A-DISCOVERY","h-n7"), t2["revision"], t2["last_event_hash"])
        self.assertIn("G09", str(cm.exception))

    def test_contract_precommit_and_descendant_after_locked_G15(self):
        c = self.reg.create_contract("C1","F300", _auth("f","A-CONTRACT-DRAFT","c-n1"), spec={"q":"test"})
        t1 = self.reg.transition_contract("C1","PRECOMMIT_REVIEW", _auth("f","A-CONTRACT-DRAFT","c-n2"), c["revision"], c["last_event_hash"])
        t2 = self.reg.transition_contract("C1","LOCKED", _auth("g","A-LOCK","c-n3"), t1["revision"], t1["last_event_hash"])
        t3 = self.reg.transition_contract("C1","DISCOVERY_ACTIVE", _auth("h","A-DISCOVERY","c-n4"), t2["revision"], t2["last_event_hash"])
        # material mutation after LOCKED directly should fail G15
        with self.assertRaises(RegistryError) as cm:
            self.reg.transition_contract("C1","DISCOVERY_CLOSED", _auth("h","A-DISCOVERY","c-n5"), t3["revision"], t3["last_event_hash"], new_spec={"q":"mutated"})
        self.assertIn("G15", str(cm.exception))
        # descendant creation should succeed and inherit debt
        desc = self.reg.create_contract_descendant("C1","C1_D1", _auth("h","A-DISCOVERY","c-n6"), spec={"q":"mutated child"})
        self.assertEqual(desc["family_root"],"F300")
        self.assertEqual(desc["debt"],1)
        # descendant debt not reset (G18) — child debt > parent
        self.assertGreater(desc["debt"],0)

class TestExperiment(unittest.TestCase):
    def setUp(self):
        self.db, self.td = _tmp_db()
        self.reg = Registry(self.db)
        self.c = self.reg.create_contract("C100","F400", _auth("a","A-CONTRACT-DRAFT","e-n1"), spec={"s":1})
        self.reg.transition_contract("C100","PRECOMMIT_REVIEW", _auth("a","A-CONTRACT-DRAFT","e-n2"), self.c["revision"], self.c["last_event_hash"])
        # need to get updated revision
        row = self.reg._get_obj_row("contract","C100")
        rev = row[4]; eh=row[5]
        self.reg.transition_contract("C100","LOCKED", _auth("b","A-LOCK","e-n3"), rev, eh)
    def tearDown(self):
        self.reg.close()
        _clean(self.db, self.td)

    def test_experiment_integrity_result_separate_G22_G05(self):
        ex = self.reg.create_experiment("EX1","C100", _auth("c","A-DISCOVERY","e-n4"))
        self.assertEqual(ex["integrity"],"NOT_CHECKED")
        # BOUND with PASS integrity but REJECTED result allowed (G05)
        t1 = self.reg.transition_experiment("EX1","BOUND", _auth("c","A-DISCOVERY","e-n5"), ex["revision"], ex["last_event_hash"], integrity="PASS", result="NONE")
        self.assertEqual(t1["integrity"],"PASS")
        t2 = self.reg.transition_experiment("EX1","READY", _auth("d","A-VALIDATE","e-n6"), t1["revision"], t1["last_event_hash"])
        t3 = self.reg.transition_experiment("EX1","RUNNING", _auth("d","A-VALIDATE","e-n7"), t2["revision"], t2["last_event_hash"])
        t4 = self.reg.transition_experiment("EX1","COMPLETED", _auth("d","A-VALIDATE","e-n8"), t3["revision"], t3["last_event_hash"], result="REJECTED")
        # integrity PASS but result REJECTED -> G05 preserved (not conflated)
        self.assertEqual(t4["integrity"],"PASS")
        self.assertEqual(t4["result"],"REJECTED")
        # invalid integrity value should fail G22
        with self.assertRaises(RegistryError):
            self.reg.transition_experiment("EX1","ADJUDICATED", _auth("e","A-GOVERN","e-n9","TD-GOVERNOR"), t4["revision"], t4["last_event_hash"], integrity="UNKNOWN")

class TestCandidateCASAndClosure(unittest.TestCase):
    def setUp(self):
        self.db, self.td = _tmp_db()
        self.reg = Registry(self.db)
        self.family = "F500"
        self.mat1 = {"model":"xgb","params":{"depth":3},"features":["a","b"]}
    def tearDown(self):
        self.reg.close()
        _clean(self.db, self.td)

    def test_candidate_frozen_closure_immutable_G01(self):
        cand = self.reg.create_candidate("CAND1", self.mat1, self.family, _auth("a","A-DISCOVERY","cand-n1"))
        t1 = self.reg.transition_candidate("CAND1","DISCOVERY_CANDIDATE","NONE", _auth("a","A-DISCOVERY","cand-n2"), cand["revision"], cand["last_event_hash"])
        # freeze with same material
        t2 = self.reg.transition_candidate("CAND1","FROZEN","NONE", _auth("b","A-VALIDATE","cand-n3"), t1["revision"], t1["last_event_hash"], material=self.mat1)
        self.assertEqual(t2["lifecycle"],"FROZEN")
        # mutate after frozen should fail G01
        bad_mat = {"model":"xgb","params":{"depth":5},"features":["a","b"]}
        with self.assertRaises(RegistryError) as cm:
            self.reg.transition_candidate("CAND1","VALIDATION_READY","NONE", _auth("b","A-VALIDATE","cand-n4"), t2["revision"], t2["last_event_hash"], material=bad_mat)
        self.assertIn("G01", str(cm.exception))
        # non-material transition after frozen should still succeed
        t3 = self.reg.transition_candidate("CAND1","VALIDATION_READY","NONE", _auth("b","A-VALIDATE","cand-n4b"), t2["revision"], t2["last_event_hash"])
        self.assertEqual(t3["lifecycle"],"VALIDATION_READY")

    def test_candidate_descendant_inherits_debt_and_not_rewrite_parent_G13_G14(self):
        cand = self.reg.create_candidate("CAND2", self.mat1, self.family, _auth("a","A-DISCOVERY","cand2-n1"))
        t1 = self.reg.transition_candidate("CAND2","DISCOVERY_CANDIDATE","NONE", _auth("a","A-DISCOVERY","cand2-n2"), cand["revision"], cand["last_event_hash"])
        t2 = self.reg.transition_candidate("CAND2","FROZEN","NONE", _auth("b","A-VALIDATE","cand2-n3"), t1["revision"], t1["last_event_hash"], material=self.mat1)
        # create descendant with mutated material
        new_mat = {"model":"xgb","params":{"depth":5},"features":["a","b"]}
        desc = self.reg.create_candidate_descendant("CAND2","CAND2_D1", new_mat, _auth("c","A-DISCOVERY","cand2-n4"))
        self.assertEqual(desc["family_root"], self.family)
        self.assertEqual(desc["debt"], 1)
        # parent still unchanged (G14)
        parent = self.reg.get_candidate("CAND2")
        child = self.reg.get_candidate("CAND2_D1")
        self.assertNotEqual(parent["root_hash"], child["root_hash"])
        self.assertEqual(parent["revision"], t2["revision"])
        # try descendant with same material should fail G14
        with self.assertRaises(RegistryError) as cm:
            self.reg.create_candidate_descendant("CAND2","CAND2_D2", self.mat1, _auth("c","A-DISCOVERY","cand2-n5"))
        self.assertIn("G14", str(cm.exception))

    def test_cas_concurrent_second_fails_G19(self):
        cand = self.reg.create_candidate("CAND3", self.mat1, self.family, _auth("a","A-DISCOVERY","cand3-n1"))
        # first transition succeeds
        t1 = self.reg.transition_candidate("CAND3","DISCOVERY_CANDIDATE","NONE", _auth("a","A-DISCOVERY","cand3-n2"), cand["revision"], cand["last_event_hash"])
        # stale expected_revision (0) should fail G19
        with self.assertRaises(RegistryError) as cm:
            self.reg.transition_candidate("CAND3","FROZEN","NONE", _auth("b","A-VALIDATE","cand3-n3"), cand["revision"], cand["last_event_hash"], material=self.mat1)
        self.assertIn("G19", str(cm.exception))
        # also stale prev hash
        with self.assertRaises(RegistryError) as cm2:
            self.reg.transition_candidate("CAND3","FROZEN","NONE", _auth("b","A-VALIDATE","cand3-n4"), t1["revision"], "0"*64, material=self.mat1)
        self.assertIn("G20", str(cm2.exception))

    def test_no_float_in_identity(self):
        bad_mat = {"model":"xgb","params":{"threshold": 3.14}}
        with self.assertRaises(RegistryError) as cm:
            self.reg.create_candidate("CAND_FLOAT", bad_mat, self.family, _auth("a","A-DISCOVERY","cand-f1"))
        self.assertIn("G01", str(cm.exception))

    def test_prev_hash_chain(self):
        cand = self.reg.create_candidate("CAND4", self.mat1, self.family, _auth("a","A-DISCOVERY","cand4-n1"))
        self.assertTrue(self.reg.verify_chain("candidate","CAND4"))
        t1 = self.reg.transition_candidate("CAND4","DISCOVERY_CANDIDATE","NONE", _auth("a","A-DISCOVERY","cand4-n2"), cand["revision"], cand["last_event_hash"])
        self.assertTrue(self.reg.verify_chain("candidate","CAND4"))

class TestCapabilityGraveyardRetention(unittest.TestCase):
    def setUp(self):
        self.db, self.td = _tmp_db()
        self.reg = Registry(self.db)
    def tearDown(self):
        self.reg.close()
        _clean(self.db, self.td)

    def test_capability_gap_requires_episode_G13(self):
        cap = self.reg.create_capability("CAP1","SENSOR", _auth("a","A-CAPABILITY","cap-n1"), family_root="F600")
        # without gap episode should fail
        with self.assertRaises(RegistryError) as cm:
            self.reg.transition_capability("CAP1","GAP_HYPOTHESIS","NONE", _auth("b","A-CAPABILITY","cap-n2"), cap["revision"], cap["last_event_hash"])
        self.assertIn("G13", str(cm.exception))
        # create supporting episode with correct disposition
        prob = self.reg.create_problem("P600","stmt", _auth("c","A-CREATE","cap-n3"), family_root="F600")
        self.reg.transition_problem("P600","OPEN", _auth("c","A-CREATE","cap-n4"), prob["revision"], prob["last_event_hash"])
        ep = self.reg.create_episode("E600","P600", _auth("d","A-CREATE","cap-n5"))
        self.reg.transition_episode("E600","CONTRACTED","NONE", _auth("d","A-LOCK","cap-n6"), ep["revision"], ep["last_event_hash"])
        t2 = self.reg.transition_episode("E600","RESEARCHING","NONE", _auth("e","A-DISCOVERY","cap-n7"), self.reg.get_episode("E600")["revision"], self.reg.get_episode("E600")["last_event_hash"])
        ep2 = self.reg.get_episode("E600")
        self.reg.transition_episode("E600","ADJUDICATED","CURRENTLY_NON_PREDICTABLE", _auth("f","A-GOVERN","cap-n8","TD-GOVERNOR"), ep2["revision"], ep2["last_event_hash"])
        # now gap with episode succeeds
        cap_row = self.reg.get_capability("CAP1")
        ok = self.reg.transition_capability("CAP1","GAP_HYPOTHESIS","NONE", _auth("b","A-CAPABILITY","cap-n9"), cap_row["revision"], cap_row["last_event_hash"], gap_episode_id="E600")
        self.assertEqual(ok["lifecycle"],"GAP_HYPOTHESIS")

    def test_graveyard_blocks_same_content_retry_G18(self):
        mat = {"model":"m1","params":{"x":1}}
        cand = self.reg.create_candidate("GRAV1", mat, "F700", _auth("a","A-DISCOVERY","grav-n1"))
        t1 = self.reg.transition_candidate("GRAV1","DISCOVERY_CANDIDATE","NONE", _auth("a","A-DISCOVERY","grav-n2"), cand["revision"], cand["last_event_hash"])
        t2 = self.reg.transition_candidate("GRAV1","FROZEN","NONE", _auth("b","A-VALIDATE","grav-n3"), t1["revision"], t1["last_event_hash"], material=mat)
        t3 = self.reg.transition_candidate("GRAV1","VALIDATION_READY","NONE", _auth("b","A-VALIDATE","grav-n4"), t2["revision"], t2["last_event_hash"])
        t4 = self.reg.transition_candidate("GRAV1","VALIDATION_ACTIVE","NONE", _auth("b","A-VALIDATE","grav-n5"), t3["revision"], t3["last_event_hash"])
        t5 = self.reg.transition_candidate("GRAV1","VALIDATION_CLOSED","NONE", _auth("b","A-VALIDATE","grav-n6"), t4["revision"], t4["last_event_hash"])
        t6 = self.reg.transition_candidate("GRAV1","ADJUDICATED","REJECTED", _auth("c","A-GOVERN","grav-n7","TD-GOVERNOR"), t5["revision"], t5["last_event_hash"])
        self.assertTrue(self.reg.is_in_graveyard("candidate","GRAV1"))
        # retry with same material should be blocked via graveyard check
        allowed = self.reg.check_graveyard_retry_allowed("candidate", mat, "F700")
        self.assertFalse(allowed)
        # materially different should be allowed
        allowed2 = self.reg.check_graveyard_retry_allowed("candidate", {"model":"m1","params":{"x":2}}, "F700")
        self.assertTrue(allowed2)

    def test_archival_does_not_change_disposition_G06_G07(self):
        mat = {"model":"m1","params":{"x":1}}
        cand = self.reg.create_candidate("ARCH1", mat, "F800", _auth("a","A-DISCOVERY","arch-n1"))
        t1 = self.reg.transition_candidate("ARCH1","DISCOVERY_CANDIDATE","NONE", _auth("a","A-DISCOVERY","arch-n2"), cand["revision"], cand["last_event_hash"])
        t2 = self.reg.transition_candidate("ARCH1","FROZEN","NONE", _auth("b","A-VALIDATE","arch-n3"), t1["revision"], t1["last_event_hash"], material=mat)
        t3 = self.reg.transition_candidate("ARCH1","VALIDATION_READY","NONE", _auth("b","A-VALIDATE","arch-n4"), t2["revision"], t2["last_event_hash"])
        before = self.reg.get_candidate("ARCH1")
        arch = self.reg.archive("candidate","ARCH1", _auth("gov","A-GOVERN","arch-n5","TD-GOVERNOR"), before["revision"], before["last_event_hash"])
        after = self.reg.get_candidate("ARCH1")
        # disposition unchanged (G06)
        self.assertEqual(before["disposition"], after["disposition"])
        self.assertEqual(before["lifecycle"], after["lifecycle"])
        self.assertEqual(after["retention"],"ARCHIVED_RECORD")
        # debt not erased (G07)
        self.assertEqual(before["debt"], after["debt"])

    def test_p001_firewall_G25(self):
        with self.assertRaises(RegistryError) as cm:
            self.reg.assert_not_p001_answer({"problem_id":"P001","answer":"profitable"})
        self.assertIn("G25", str(cm.exception))
        # non-P001 allowed
        self.reg.assert_not_p001_answer({"problem_id":"P002","answer":"something"})

    def test_descendant_inherits_debt_G13(self):
        mat = {"model":"m","params":{"a":1}}
        cand = self.reg.create_candidate("DEBT1", mat, "F900", _auth("a","A-DISCOVERY","debt-n1"))
        desc = self.reg.create_candidate_descendant("DEBT1","DEBT1_D1", {"model":"m","params":{"a":2}}, _auth("b","A-DISCOVERY","debt-n2"))
        self.assertEqual(desc["debt"], 1)
        desc2 = self.reg.create_candidate_descendant("DEBT1_D1","DEBT1_D2", {"model":"m","params":{"a":3}}, _auth("c","A-DISCOVERY","debt-n3"))
        self.assertEqual(desc2["debt"], 2)
        # new ID with same family cannot reset debt to 0
        # create fresh candidate with same family but via create_candidate (not descendant) still inherits family debt 0? Actually family_debt table keeps max; descendant path increased family debt to 2, so next create in same family should see debt 2? In our impl create_candidate reads family_debt max.
        # Let's check: create new candidate same family should have debt 2 (not 0) — G18
        # But our create_candidate reads existing family_debt; after descendants, family_debt is 2
        cand2 = self.reg.create_candidate("DEBT_NEW", {"model":"m","params":{"a":9}}, "F900", _auth("d","A-DISCOVERY","debt-n4"))
        # Should have debt 2 (inherited, not reset)
        self.assertEqual(cand2["debt"], 2)

if __name__ == "__main__":
    unittest.main(verbosity=2)
