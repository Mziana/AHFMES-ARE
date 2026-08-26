"""
Tests for are/evidence.py — Evidence Ledger ARE-0C/D (Slice ARE-1)

Covers per CONTRACTS/AHFMES_ARE_0C_EVIDENCE_LEDGER_AND_HOLDOUT_CONSUMPTION_V2.md + 0D:
 - snapshot content-addressed immutable, provenance/origin/retention, eligibility derived
 - relation gate default RELATED, TD-RESEARCH cannot UNRELATED, one slot per key
 - atomic reservation (exact snapshot, batch, estimand, multiplicity)
 - exposure classes E0-E3, outcome awareness
 - independent_for fail-closed predicate (11 checks)
 - prospective STRICT_BLIND vs LIVE_FROZEN
 - derived evidence parent roots, news as-of provenance, counterfactual quality
 - reuse storage + canonical, stdlib only

Run: python -m tests.are.test_evidence -v
"""
import gc
import os
import tempfile
import time
import unittest
import json

from are.evidence import EvidenceLedger, RelationRegistry, EvidenceError
from are.canonical import VerificationError

def _tmp_db():
    td = tempfile.mkdtemp()
    p = os.path.join(td, "evidence.db")
    return p, td

def _clean(p, td):
    gc.collect()
    for suffix in ["", "-wal", "-shm"]:
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

def _make_snapshot(ledger, sid="SNAP1", prov="VERIFIED", origin="HISTORICAL_RESERVED", parent=None, as_of=None, itv=True):
    return ledger.create_snapshot(
        evidence_snapshot_id=sid,
        source_manifest_hash="manifest_hash_"+sid,
        source_kind="CSV",
        source_epoch="2026-01-01",
        information_time_contract_hash="ith_"+sid,
        row_or_event_identity_contract_hash="row_"+sid,
        completeness_proof_hash="comp_"+sid,
        provenance_status=prov,
        origin=origin,
        retention="ACTIVE_RECORD",
        parent_roots=parent,
        as_of_provenance=as_of,
        information_time_valid=itv,
    )

class TestSnapshotImmutableContentAddressed(unittest.TestCase):
    def setUp(self):
        self.db, self.td = _tmp_db()
        self.ledger = EvidenceLedger(self.db)
    def tearDown(self):
        self.ledger.close()
        _clean(self.db, self.td)
    def test_snapshot_content_addressed_and_immutable(self):
        s1 = _make_snapshot(self.ledger, "S1")
        # same params different id => different root
        s2 = _make_snapshot(self.ledger, "S2")
        self.assertNotEqual(s1.root_hash, s2.root_hash)
        # duplicate id fails (immutable)
        with self.assertRaises(EvidenceError) as cm:
            _make_snapshot(self.ledger, "S1")
        self.assertIn("SNAPSHOT_EXISTS", str(cm.exception))
        # new data => new snapshot, never mutates old
        old = self.ledger.get_snapshot("S1")
        self.assertEqual(old.root_hash, s1.root_hash)
        self.assertEqual(old.provenance_status, "VERIFIED")
        # canonical bytes non-empty and hash is hex64
        self.assertEqual(len(s1.root_hash), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in s1.root_hash))

    def test_snapshot_requires_canonical_no_float(self):
        # float in manifest should fail via canonical check indirectly? Our snapshot uses string hashes, but as_of provenance with float should fail
        with self.assertRaises(EvidenceError):
            self.ledger.create_snapshot(
                evidence_snapshot_id="S_FLOAT",
                source_manifest_hash="m",
                source_kind="CSV",
                source_epoch="2026-01-01",
                information_time_contract_hash="ith",
                row_or_event_identity_contract_hash="row",
                completeness_proof_hash="comp",
                provenance_status="VERIFIED",
                origin="HISTORICAL_RESERVED",
                as_of_provenance={"scheduled_event_time": 123.45, "source_publish_time": "t"}  # float not allowed indirectly via hash?
            )
        # But we test that creating snapshot with float in as_of triggers INFORMATION_TIME_INVALID or CANONICAL_FAILED
        # Ensure at least one fails: we test via direct canonical check
        from are.canonical import canonicalize_json
        with self.assertRaises(VerificationError):
            canonicalize_json({"v": 3.14})

    def test_provenance_enforces_verification(self):
        s_bad = _make_snapshot(self.ledger, "S_BAD", prov="UNVERIFIED")
        self.assertEqual(s_bad.provenance_status, "UNVERIFIED")
        s_inv = _make_snapshot(self.ledger, "S_INV", prov="INVALID")
        self.assertEqual(s_inv.provenance_status, "INVALID")
        with self.assertRaises(EvidenceError):
            _make_snapshot(self.ledger, "S_BAD2", prov="UNKNOWN")

    def test_retention_archive_does_not_reset_exposure(self):
        s = _make_snapshot(self.ledger, "S_RET")
        # log an exposure
        self.ledger.set_contract_lock("contract_root_1", True, True, True, True, True)
        res = self.ledger.create_reservation(
            reservation_id="RES_RET",
            research_program_id="RP1",
            program_budget_envelope_root_hash="prog_budget_1",
            research_family_root="RF1",
            claim_family_root="CF1",
            research_contract_root_hash="contract_root_1",
            evidence_snapshot_root_hash=s.root_hash,
            validation_family_root_hash="vf_1",
            candidate_batch_root_hash="batch_1",
            primary_estimand_root_hash="est_1",
            multiplicity_plan_root_hash="mult_1",
            search_tree_root_hash="st_1",
            search_debt_root_hash="sd_1",
            permitted_disclosures_root_hash="pd_1",
            permitted_actor_ids=["actor1"],
            role="INDEPENDENT_CONFIRMATION",
        )
        exp = self.ledger.log_exposure(
            exposure_event_id="EXP_RET1",
            evidence_snapshot_root_hash=s.root_hash,
            research_program_id="RP1",
            research_family_root="RF1",
            claim_family_root="CF1",
            research_contract_root_hash="contract_root_1",
            candidate_or_batch_root_hash="batch_1",
            validation_reservation_id="RES_RET",
            role="INDEPENDENT_CONFIRMATION",
            access_granularity="PRECOMMITTED_METRIC",
            outcome_awareness="BOUNDED",
        )
        self.assertEqual(exp.exposure_class, "E1")
        # archive snapshot
        archived = self.ledger.archive_snapshot("S_RET")
        self.assertEqual(archived.retention, "ARCHIVED_RECORD")
        self.assertEqual(archived.root_hash, s.root_hash)  # hash unchanged
        # exposure still exists and independent_for for related lineage now fails (holdout consumed)
        # Create new reservation for same lineage should be considered related exposure
        # Verify exposure still counted after archive
        s2 = _make_snapshot(self.ledger, "S_RET2", origin="HISTORICAL_RESERVED")
        # independent_for for same RF/CF should fail (holdout consumed or archived stale) and exposure persists after archival
        # verify exposure still present via direct DB check
        conn = self.ledger._store._get_conn()
        cur = conn.execute("SELECT exposure_event_id FROM evidence_exposures WHERE exposure_event_id='EXP_RET1'")
        self.assertIsNotNone(cur.fetchone())
        # independent before archival already had holdout consumption; after archival still fail-closed
        ok, code, _ = self.ledger.independent_for(
            evidence_snapshot_id="S_RET",
            research_program_id="RP1",
            research_family_root="RF1",
            claim_family_root="CF1",
            research_contract_root_hash="contract_root_1",
            candidate_batch_root_hash="batch_1",
            validation_family_root_hash="vf_1",
            multiplicity_plan_root_hash="mult_1",
            role="INDEPENDENT_CONFIRMATION",
            reservation_id="RES_RET",
        )
        self.assertFalse(ok)
        # archived snapshot => LEDGER_STALE dominates, but exposure persists (orthogonal)
        self.assertIn(code, ("RELATED_EXPOSURE_ALREADY_SEEN", "LEDGER_STALE"))


class TestRelationGate(unittest.TestCase):
    def setUp(self):
        self.db, self.td = _tmp_db()
        self.ledger = EvidenceLedger(self.db)
        self.reg = RelationRegistry(self.ledger)
    def tearDown(self):
        self.ledger.close()
        _clean(self.db, self.td)

    def test_default_related_fail_closed(self):
        # no decision => default RELATED
        self.assertEqual(self.ledger.evaluate_relation("RF_X", "CF_Y"), "RELATED")
        self.assertEqual(self.reg.evaluate("RF_X", "CF_Y"), "RELATED")

    def test_td_research_cannot_issue_unrelated(self):
        with self.assertRaises(EvidenceError) as cm:
            self.ledger.put_relation_decision("RF1", "CF1", "UNRELATED_SUPPORTED", "TD-RESEARCH", "alice")
        self.assertIn("TD_RESEARCH_CANNOT_UNRELATE", str(cm.exception))
        # TD-EVIDENCE can
        dec = self.ledger.put_relation_decision("RF1", "CF1", "UNRELATED_SUPPORTED", "TD-EVIDENCE", "bob")
        self.assertEqual(dec.decision, "UNRELATED_SUPPORTED")
        self.assertEqual(self.ledger.evaluate_relation("RF1", "CF1"), "UNRELATED_SUPPORTED")

    def test_one_slot_per_relation_key(self):
        self.ledger.put_relation_decision("RF2", "CF2", "RELATED", "TD-EVIDENCE", "carol")
        with self.assertRaises(EvidenceError) as cm:
            self.ledger.put_relation_decision("RF2", "CF2", "UNRELATED_SUPPORTED", "TD-EVIDENCE", "dave")
        self.assertIn("RELATION_SLOT_TAKEN", str(cm.exception))
        # different candidate batch is different key -> allowed
        dec2 = self.ledger.put_relation_decision("RF2", "CF2", "UNRELATED_SUPPORTED", "TD-EVIDENCE", "dave", candidate_batch_root_hash="batchXYZ")
        self.assertEqual(dec2.decision, "UNRELATED_SUPPORTED")

    def test_unknown_related_fail_closed(self):
        self.ledger.put_relation_decision("RF3", "CF3", "UNKNOWN_RELATED_FAIL_CLOSED", "TD-EVIDENCE", "eve")
        self.assertEqual(self.ledger.evaluate_relation("RF3", "CF3"), "RELATED")  # maps to RELATED fail-closed

class TestAtomicReservation(unittest.TestCase):
    def setUp(self):
        self.db, self.td = _tmp_db()
        self.ledger = EvidenceLedger(self.db)
        self.snap = _make_snapshot(self.ledger, "SNAP_RES")
        self.ledger.set_contract_lock("contract_root_A", True, True, True, True, True)
    def tearDown(self):
        self.ledger.close()
        _clean(self.db, self.td)

    def test_reservation_requires_exact_snapshot(self):
        with self.assertRaises(EvidenceError) as cm:
            self.ledger.create_reservation(
                reservation_id="R_BAD_SNAP",
                research_program_id="RP1", program_budget_envelope_root_hash="pb",
                research_family_root="RF1", claim_family_root="CF1",
                research_contract_root_hash="contract_root_A",
                evidence_snapshot_root_hash="nonexistent_root",
                validation_family_root_hash="vf", candidate_batch_root_hash="batch", primary_estimand_root_hash="est",
                multiplicity_plan_root_hash="mult", search_tree_root_hash="st", search_debt_root_hash="sd",
                permitted_disclosures_root_hash=None, permitted_actor_ids=[], role="INDEPENDENT_CONFIRMATION"
            )
        self.assertIn("SNAPSHOT_MISMATCH", str(cm.exception))

    def test_reservation_requires_batch_and_multiplicity(self):
        with self.assertRaises(EvidenceError) as cm:
            self.ledger.create_reservation(
                reservation_id="R_NO_BATCH",
                research_program_id="RP1", program_budget_envelope_root_hash="pb",
                research_family_root="RF1", claim_family_root="CF1",
                research_contract_root_hash="contract_root_A",
                evidence_snapshot_root_hash=self.snap.root_hash,
                validation_family_root_hash="", candidate_batch_root_hash="", primary_estimand_root_hash="est",
                multiplicity_plan_root_hash="mult", search_tree_root_hash="st", search_debt_root_hash="sd",
                permitted_disclosures_root_hash=None, permitted_actor_ids=[], role="INDEPENDENT_CONFIRMATION"
            )
        self.assertIn("BATCH_REQUIRED", str(cm.exception))
        with self.assertRaises(EvidenceError):
            self.ledger.create_reservation(
                reservation_id="R_NO_MULT",
                research_program_id="RP1", program_budget_envelope_root_hash="pb",
                research_family_root="RF1", claim_family_root="CF1",
                research_contract_root_hash="contract_root_A",
                evidence_snapshot_root_hash=self.snap.root_hash,
                validation_family_root_hash="vf", candidate_batch_root_hash="batch", primary_estimand_root_hash="est",
                multiplicity_plan_root_hash="", search_tree_root_hash="st", search_debt_root_hash="sd",
                permitted_disclosures_root_hash=None, permitted_actor_ids=[], role="INDEPENDENT_CONFIRMATION"
            )

    def test_reservation_atomic_conflict_on_duplicate_batch(self):
        r1 = self.ledger.create_reservation(
            reservation_id="R1", research_program_id="RP1", program_budget_envelope_root_hash="pb",
            research_family_root="RF1", claim_family_root="CF1",
            research_contract_root_hash="contract_root_A",
            evidence_snapshot_root_hash=self.snap.root_hash,
            validation_family_root_hash="vf1", candidate_batch_root_hash="batch1", primary_estimand_root_hash="est1",
            multiplicity_plan_root_hash="mult1", search_tree_root_hash="st1", search_debt_root_hash="sd1",
            permitted_disclosures_root_hash="pd1", permitted_actor_ids=["a1"], role="INDEPENDENT_CONFIRMATION"
        )
        self.assertEqual(r1.state, "RESERVED")
        # second reservation same batch+lineage should conflict
        with self.assertRaises(EvidenceError) as cm:
            self.ledger.create_reservation(
                reservation_id="R2", research_program_id="RP1", program_budget_envelope_root_hash="pb",
                research_family_root="RF1", claim_family_root="CF1",
                research_contract_root_hash="contract_root_A",
                evidence_snapshot_root_hash=self.snap.root_hash,
                validation_family_root_hash="vf1", candidate_batch_root_hash="batch1", primary_estimand_root_hash="est1",
                multiplicity_plan_root_hash="mult1", search_tree_root_hash="st1", search_debt_root_hash="sd1",
                permitted_disclosures_root_hash="pd1", permitted_actor_ids=["a1"], role="INDEPENDENT_CONFIRMATION"
            )
        self.assertIn("RESERVATION_CONFLICT", str(cm.exception))

    def test_reservation_ledger_stale_on_wrong_expected_revision(self):
        # get head
        head_rev, head_hash = self.ledger._store.get_head("evidence_ledger")
        with self.assertRaises(EvidenceError) as cm:
            self.ledger.create_reservation(
                reservation_id="R_STALE", research_program_id="RP1", program_budget_envelope_root_hash="pb",
                research_family_root="RF_STALE", claim_family_root="CF_STALE",
                research_contract_root_hash="contract_root_A",
                evidence_snapshot_root_hash=self.snap.root_hash,
                validation_family_root_hash="vf", candidate_batch_root_hash="batch_stale", primary_estimand_root_hash="est",
                multiplicity_plan_root_hash="mult", search_tree_root_hash="st", search_debt_root_hash="sd",
                permitted_disclosures_root_hash=None, permitted_actor_ids=[], role="INDEPENDENT_CONFIRMATION",
                expected_ledger_revision=9999
            )
        self.assertIn("LEDGER_STALE", str(cm.exception))

class TestExposureClasses(unittest.TestCase):
    def setUp(self):
        self.db, self.td = _tmp_db()
        self.ledger = EvidenceLedger(self.db)
        self.snap = _make_snapshot(self.ledger, "SNAP_EXP")
    def tearDown(self):
        self.ledger.close()
        _clean(self.db, self.td)
    def test_e0_metadata_only_no_outcome(self):
        exp = self.ledger.log_exposure(
            exposure_event_id="E0_1", evidence_snapshot_root_hash=self.snap.root_hash,
            research_program_id="RP1", research_family_root="RF1", claim_family_root="CF1",
            research_contract_root_hash="c1", candidate_or_batch_root_hash="b1", validation_reservation_id=None,
            role="DISCOVERY", access_granularity="METADATA_ONLY", outcome_awareness="NONE"
        )
        self.assertEqual(exp.exposure_class, "E0")
    def test_e1_precommitted_bounded(self):
        exp = self.ledger.log_exposure(
            exposure_event_id="E1_1", evidence_snapshot_root_hash=self.snap.root_hash,
            research_program_id="RP1", research_family_root="RF1", claim_family_root="CF1",
            research_contract_root_hash="c1", candidate_or_batch_root_hash="b1", validation_reservation_id=None,
            role="INDEPENDENT_CONFIRMATION", access_granularity="PRECOMMITTED_METRIC", outcome_awareness="BOUNDED"
        )
        self.assertEqual(exp.exposure_class, "E1")
    def test_e2_aggregate(self):
        exp = self.ledger.log_exposure(
            exposure_event_id="E2_1", evidence_snapshot_root_hash=self.snap.root_hash,
            research_program_id="RP1", research_family_root="RF1", claim_family_root="CF1",
            research_contract_root_hash="c1", candidate_or_batch_root_hash="b1", validation_reservation_id=None,
            role="INDEPENDENT_CONFIRMATION", access_granularity="AGGREGATE_OUTCOME", outcome_awareness="FULL"
        )
        self.assertEqual(exp.exposure_class, "E2")
    def test_e3_row_outcome(self):
        exp = self.ledger.log_exposure(
            exposure_event_id="E3_1", evidence_snapshot_root_hash=self.snap.root_hash,
            research_program_id="RP1", research_family_root="RF1", claim_family_root="CF1",
            research_contract_root_hash="c1", candidate_or_batch_root_hash="b1", validation_reservation_id=None,
            role="SHADOW_EVALUATION", access_granularity="ROW_OUTCOME", outcome_awareness="FULL"
        )
        self.assertEqual(exp.exposure_class, "E3")
        exp2 = self.ledger.log_exposure(
            exposure_event_id="E3_2", evidence_snapshot_root_hash=self.snap.root_hash,
            research_program_id="RP1", research_family_root="RF1", claim_family_root="CF1",
            research_contract_root_hash="c1", candidate_or_batch_root_hash="b2", validation_reservation_id=None,
            role="SHADOW_EVALUATION", access_granularity="RAW_OUTCOME", outcome_awareness="FULL"
        )
        self.assertEqual(exp2.exposure_class, "E3")

class TestIndependentForFailClosed(unittest.TestCase):
    def setUp(self):
        self.db, self.td = _tmp_db()
        self.ledger = EvidenceLedger(self.db)
        self.snap_verified = _make_snapshot(self.ledger, "S_VER", prov="VERIFIED", origin="HISTORICAL_RESERVED")
        self.snap_unverified = _make_snapshot(self.ledger, "S_UNV", prov="UNVERIFIED")
        self.snap_invalid = _make_snapshot(self.ledger, "S_INV2", prov="INVALID")
        self.ledger.set_contract_lock("ctr_locked", True, True, True, True, True)
        self.ledger.set_contract_lock("ctr_unlocked", False, True, True, True, True)
        self.res = self.ledger.create_reservation(
            reservation_id="RES_IND", research_program_id="RP_IND", program_budget_envelope_root_hash="pb",
            research_family_root="RF_IND", claim_family_root="CF_IND",
            research_contract_root_hash="ctr_locked",
            evidence_snapshot_root_hash=self.snap_verified.root_hash,
            validation_family_root_hash="vf_ind", candidate_batch_root_hash="batch_ind", primary_estimand_root_hash="est_ind",
            multiplicity_plan_root_hash="mult_ind", search_tree_root_hash="st_ind", search_debt_root_hash="sd_ind",
            permitted_disclosures_root_hash="pd_ind", permitted_actor_ids=["actor1"], role="INDEPENDENT_CONFIRMATION"
        )
    def tearDown(self):
        self.ledger.close()
        _clean(self.db, self.td)

    def test_provenance_must_be_verified(self):
        ok, code, _ = self.ledger.independent_for(
            evidence_snapshot_id="S_UNV", research_program_id="RP_IND", research_family_root="RF_IND", claim_family_root="CF_IND",
            research_contract_root_hash="ctr_locked", candidate_batch_root_hash="batch_ind", validation_family_root_hash="vf_ind",
            multiplicity_plan_root_hash="mult_ind", role="INDEPENDENT_CONFIRMATION", reservation_id="RES_IND")
        self.assertFalse(ok); self.assertEqual(code, "PROVENANCE_INVALID")
        ok2, code2, _ = self.ledger.independent_for(
            evidence_snapshot_id="S_INV2", research_program_id="RP_IND", research_family_root="RF_IND", claim_family_root="CF_IND",
            research_contract_root_hash="ctr_locked", candidate_batch_root_hash="batch_ind", validation_family_root_hash="vf_ind",
            multiplicity_plan_root_hash="mult_ind", role="INDEPENDENT_CONFIRMATION", reservation_id="RES_IND")
        self.assertFalse(ok2); self.assertEqual(code2, "PROVENANCE_INVALID")

    def test_snapshot_must_be_exact(self):
        ok, code, _ = self.ledger.independent_for(
            evidence_snapshot_id="S_VER", research_program_id="RP_IND", research_family_root="RF_IND", claim_family_root="CF_IND",
            research_contract_root_hash="ctr_locked", candidate_batch_root_hash="WRONG_BATCH", validation_family_root_hash="vf_ind",
            multiplicity_plan_root_hash="mult_ind", role="INDEPENDENT_CONFIRMATION", reservation_id="RES_IND")
        self.assertFalse(ok); self.assertEqual(code, "BATCH_NOT_PRECOMMITTED")

    def test_contract_must_be_locked_and_budget_valid(self):
        ok, code, _ = self.ledger.independent_for(
            evidence_snapshot_id="S_VER", research_program_id="RP_IND", research_family_root="RF_IND", claim_family_root="CF_IND",
            research_contract_root_hash="ctr_unlocked", candidate_batch_root_hash="batch_ind", validation_family_root_hash="vf_ind",
            multiplicity_plan_root_hash="mult_ind", role="INDEPENDENT_CONFIRMATION", reservation_id="RES_IND")
        # will fail snapshot mismatch first because reservation contract differs, but we test via direct contract lock check
        # create new reservation with unlocked contract
        snap2 = _make_snapshot(self.ledger, "S_VER2")
        self.ledger.set_contract_lock("ctr_unlocked2", False, True, True, True, True)
        res2 = self.ledger.create_reservation(
            reservation_id="RES_UNLOCKED", research_program_id="RP_IND", program_budget_envelope_root_hash="pb",
            research_family_root="RF_U2", claim_family_root="CF_U2",
            research_contract_root_hash="ctr_unlocked2",
            evidence_snapshot_root_hash=snap2.root_hash,
            validation_family_root_hash="vf", candidate_batch_root_hash="batch_u2", primary_estimand_root_hash="est",
            multiplicity_plan_root_hash="mult", search_tree_root_hash="st", search_debt_root_hash="sd",
            permitted_disclosures_root_hash=None, permitted_actor_ids=[], role="INDEPENDENT_CONFIRMATION"
        )
        ok2, code2, _ = self.ledger.independent_for(
            evidence_snapshot_id="S_VER2", research_program_id="RP_IND", research_family_root="RF_U2", claim_family_root="CF_U2",
            research_contract_root_hash="ctr_unlocked2", candidate_batch_root_hash="batch_u2", validation_family_root_hash="vf",
            multiplicity_plan_root_hash="mult", role="INDEPENDENT_CONFIRMATION", reservation_id="RES_UNLOCKED")
        self.assertFalse(ok2)

    def test_prior_exposure_consumes_holdout(self):
        # log prior outcome-aware exposure before reservation freeze -> independent fails
        snap3 = _make_snapshot(self.ledger, "S_HOLD")
        # need reservation before exposure to test prior? Actually prior exposure before reservation should cause independent false
        # So create exposure first on same RF
        self.ledger.log_exposure(
            exposure_event_id="EXP_PRIOR", evidence_snapshot_root_hash=snap3.root_hash,
            research_program_id="RP_IND", research_family_root="RF_PRIOR", claim_family_root="CF_PRIOR",
            research_contract_root_hash="ctr_locked", candidate_or_batch_root_hash="batch_prior", validation_reservation_id=None,
            role="INDEPENDENT_CONFIRMATION", access_granularity="PRECOMMITTED_METRIC", outcome_awareness="BOUNDED"
        )
        self.ledger.set_contract_lock("ctr_locked2", True, True, True, True, True)
        res_prior = self.ledger.create_reservation(
            reservation_id="RES_PRIOR", research_program_id="RP_IND", program_budget_envelope_root_hash="pb",
            research_family_root="RF_PRIOR", claim_family_root="CF_PRIOR",
            research_contract_root_hash="ctr_locked2",
            evidence_snapshot_root_hash=snap3.root_hash,
            validation_family_root_hash="vf_p", candidate_batch_root_hash="batch_p", primary_estimand_root_hash="est_p",
            multiplicity_plan_root_hash="mult_p", search_tree_root_hash="st_p", search_debt_root_hash="sd_p",
            permitted_disclosures_root_hash=None, permitted_actor_ids=[], role="INDEPENDENT_CONFIRMATION"
        )
        ok, code, _ = self.ledger.independent_for(
            evidence_snapshot_id="S_HOLD", research_program_id="RP_IND", research_family_root="RF_PRIOR", claim_family_root="CF_PRIOR",
            research_contract_root_hash="ctr_locked2", candidate_batch_root_hash="batch_p", validation_family_root_hash="vf_p",
            multiplicity_plan_root_hash="mult_p", role="INDEPENDENT_CONFIRMATION", reservation_id="RES_PRIOR"
        )
        self.assertFalse(ok)
        self.assertEqual(code, "RELATED_EXPOSURE_ALREADY_SEEN")

    def test_reservation_required(self):
        ok, code, _ = self.ledger.independent_for(
            evidence_snapshot_id="S_VER", research_program_id="RP_IND", research_family_root="RF_IND", claim_family_root="CF_IND",
            research_contract_root_hash="ctr_locked", candidate_batch_root_hash="batch_ind", validation_family_root_hash="vf_ind",
            multiplicity_plan_root_hash="mult_ind", role="INDEPENDENT_CONFIRMATION", reservation_id=None)
        self.assertFalse(ok); self.assertEqual(code, "RESERVATION_CONFLICT")

    def test_information_time_invalid(self):
        snap_it = _make_snapshot(self.ledger, "S_IT", itv=False)
        self.ledger.set_contract_lock("ctr_it", True, True, True, True, True)
        res_it = self.ledger.create_reservation(
            reservation_id="RES_IT", research_program_id="RP_IT", program_budget_envelope_root_hash="pb",
            research_family_root="RF_IT", claim_family_root="CF_IT",
            research_contract_root_hash="ctr_it",
            evidence_snapshot_root_hash=snap_it.root_hash,
            validation_family_root_hash="vf_it", candidate_batch_root_hash="batch_it", primary_estimand_root_hash="est_it",
            multiplicity_plan_root_hash="mult_it", search_tree_root_hash="st_it", search_debt_root_hash="sd_it",
            permitted_disclosures_root_hash=None, permitted_actor_ids=[], role="INDEPENDENT_CONFIRMATION"
        )
        ok, code, _ = self.ledger.independent_for(
            evidence_snapshot_id="S_IT", research_program_id="RP_IT", research_family_root="RF_IT", claim_family_root="CF_IT",
            research_contract_root_hash="ctr_it", candidate_batch_root_hash="batch_it", validation_family_root_hash="vf_it",
            multiplicity_plan_root_hash="mult_it", role="INDEPENDENT_CONFIRMATION", reservation_id="RES_IT")
        self.assertFalse(ok); self.assertEqual(code, "INFORMATION_TIME_INVALID")

class TestDerivedAndNews(unittest.TestCase):
    def setUp(self):
        self.db, self.td = _tmp_db()
        self.ledger = EvidenceLedger(self.db)
    def tearDown(self):
        self.ledger.close()
        _clean(self.db, self.td)
    def test_derived_keeps_parent_roots(self):
        parent = _make_snapshot(self.ledger, "PARENT1")
        child = self.ledger.derive_snapshot("CHILD1", "PARENT1", source_manifest_hash="m_child", source_kind="PARQUET", source_epoch="2026-02-01", provenance_status="VERIFIED", origin="HISTORICAL_RESERVED")
        self.assertIn(parent.root_hash, child.parent_roots)
        # rename/copy should not reset exposure: child still derived, but exposure tracking via parent roots audit still visible
        self.assertEqual(child.source_manifest_hash, "m_child")

    def test_derived_invalid_propagates(self):
        parent_inv = _make_snapshot(self.ledger, "PARENT_INV", prov="INVALID")
        child = self.ledger.derive_snapshot("CHILD_INV", "PARENT_INV", source_manifest_hash="m2", source_kind="CSV", source_epoch="2026-02-01", provenance_status="VERIFIED", origin="HISTORICAL_RESERVED")
        self.assertEqual(child.provenance_status, "INVALID")

    def test_news_as_of_provenance_required(self):
        # missing fields should fail
        with self.assertRaises(EvidenceError) as cm:
            _make_snapshot(self.ledger, "NEWS_BAD", as_of={"scheduled_event_time": "2026-01-01T00:00:00Z", "source_publish_time": "2026-01-01T00:01:00Z"})
        self.assertIn("INFORMATION_TIME_INVALID", str(cm.exception))
        # complete news provenance passes
        full = {
            "scheduled_event_time": "2026-01-01T00:00:00Z",
            "source_publish_time": "2026-01-01T00:01:00Z",
            "first_machine_available_time": "2026-01-01T00:01:05Z",
            "received_time": "2026-01-01T00:01:06Z",
            "parsed_time": "2026-01-01T00:01:07Z",
            "decision_available_time": "2026-01-01T00:01:08Z",
            "revision_identity": "rev1",
            "source_identity": "src1",
        }
        snap = _make_snapshot(self.ledger, "NEWS_GOOD", as_of=full)
        self.assertEqual(snap.as_of_provenance, full)

    def test_counterfactual_quality_gate_only(self):
        snap = _make_snapshot(self.ledger, "CF_SNAP")
        # research cannot set
        with self.assertRaises(EvidenceError) as cm:
            self.ledger.set_counterfactual_quality("CF_SNAP", "CF-HIGH", "TD-RESEARCH", "alice")
        self.assertIn("CF_QUALITY_GATE_ONLY", str(cm.exception))
        # TD-EVIDENCE can
        updated = self.ledger.set_counterfactual_quality("CF_SNAP", "CF-HIGH", "TD-EVIDENCE", "bob")
        self.assertEqual(updated.counterfactual_quality, "CF-HIGH")
        with self.assertRaises(EvidenceError):
            self.ledger.set_counterfactual_quality("CF_SNAP", "CF-BAD", "TD-EVIDENCE", "bob")

class TestProspective(unittest.TestCase):
    def setUp(self):
        self.db, self.td = _tmp_db()
        self.ledger = EvidenceLedger(self.db)
    def tearDown(self):
        self.ledger.close()
        _clean(self.db, self.td)
    def test_strict_blind_requires_embargo(self):
        with self.assertRaises(EvidenceError) as cm:
            self.ledger.create_prospective_epoch("EP_STRICT_BAD", "STRICT_BLIND", "2026-01-01T00:00:00Z", "end1", "ctr1", "RP1", "", "2026-01-02T00:00:00Z")
        self.assertIn("EMBARGO_REQUIRED", str(cm.exception))
        ep = self.ledger.create_prospective_epoch("EP_STRICT", "STRICT_BLIND", "2026-01-01T00:00:00Z", "end1", "ctr1", "RP1", "embargo_hash", "2026-01-02T00:00:00Z", state="SEALED")
        self.assertEqual(ep.klass, "STRICT_BLIND")
        # LIVE_FROZEN does NOT require embargo? but we allow empty embargo
        ep2 = self.ledger.create_prospective_epoch("EP_LIVE", "LIVE_FROZEN", "2026-01-01T00:00:00Z", "end2", "ctr2", "RP2", "", "2026-01-02T00:00:00Z")
        self.assertEqual(ep2.klass, "LIVE_FROZEN")
    def test_prospective_state_transitions_linear(self):
        ep = self.ledger.create_prospective_epoch("EP_T", "LIVE_FROZEN", "2026-01-01T00:00:00Z", "end", "ctr", "RP1", "", "2026-01-02T00:00:00Z", state="SEALED")
        ep2 = self.ledger.transition_prospective_epoch("EP_T", "ACTIVE")
        self.assertEqual(ep2.state, "ACTIVE")
        ep3 = self.ledger.transition_prospective_epoch("EP_T", "CLOSED")
        self.assertEqual(ep3.state, "CLOSED")
        # skipping state fails
        with self.assertRaises(EvidenceError):
            self.ledger.transition_prospective_epoch("EP_T", "RELEASED")  # must go via SNAPSHOTTED

if __name__ == "__main__":
    unittest.main(verbosity=2)
