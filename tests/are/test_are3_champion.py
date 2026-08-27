"""
Unit Tests for AHFMES ARE-3 Champion Registry (ACC-323, ACC-324, ACC-325)
"""

import os
import tempfile
import unittest

from are.champion import ChampionRecord, ChampionRegistry
from are.governor import PromotionDisposition
from are.storage import EventStore


class TestChampionRegistry(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "champion_test.db")
        self.store = EventStore(self.db_path)
        self.registry = ChampionRegistry(self.store)

    def tearDown(self):
        self.store.close()
        self.tmp_dir.cleanup()

    def test_initial_state_no_active_champion(self):
        self.assertIsNone(self.registry.get_active_champion())

    def test_promotion_valid_and_lineage_tracking(self):
        disp1 = PromotionDisposition(
            candidate_id="CAND_001",
            champion_id="GENESIS",
            decision="PROMOTED",
            rationale="Defeated genesis",
            governor_signature="SIG_VALID_1",
            timestamp=1000.0,
        )

        champ1 = self.registry.promote_champion("CAND_001", disp1)
        self.assertIsInstance(champ1, ChampionRecord)
        self.assertEqual(champ1.candidate_id, "CAND_001")
        self.assertEqual(champ1.status, "ACTIVE")

        active = self.registry.get_active_champion()
        self.assertIsNotNone(active)
        self.assertEqual(active.champion_id, champ1.champion_id)

        # Promote second champion
        disp2 = PromotionDisposition(
            candidate_id="CAND_002",
            champion_id=champ1.champion_id,
            decision="PROMOTED",
            rationale="Defeated champ1",
            governor_signature="SIG_VALID_2",
            timestamp=2000.0,
        )
        champ2 = self.registry.promote_champion("CAND_002", disp2)
        active2 = self.registry.get_active_champion()
        self.assertEqual(active2.champion_id, champ2.champion_id)
        self.assertEqual(active2.candidate_id, "CAND_002")

        lineage = self.registry.list_champion_lineage()
        self.assertEqual(len(lineage), 2)

    def test_unauthorized_promotion_raises(self):
        disp_dismissed = PromotionDisposition(
            candidate_id="CAND_FAIL",
            champion_id="GENESIS",
            decision="DISMISSED",
            rationale="Failed critic",
            governor_signature="SIG_VALID",
            timestamp=1000.0,
        )

        with self.assertRaises(ValueError) as ctx1:
            self.registry.promote_champion("CAND_FAIL", disp_dismissed)
        self.assertIn("Unauthorized promotion attempt", str(ctx1.exception))

        disp_mismatch = PromotionDisposition(
            candidate_id="CAND_A",
            champion_id="GENESIS",
            decision="PROMOTED",
            rationale="Pass",
            governor_signature="SIG_VALID",
            timestamp=1000.0,
        )
        with self.assertRaises(ValueError) as ctx2:
            self.registry.promote_champion("CAND_B", disp_mismatch)
        self.assertIn("candidate mismatch", str(ctx2.exception))

    def test_rollback_champion_restores_previous(self):
        disp1 = PromotionDisposition(
            candidate_id="CAND_V1",
            champion_id="GENESIS",
            decision="PROMOTED",
            rationale="V1 pass",
            governor_signature="SIG1",
            timestamp=1000.0,
        )
        c1 = self.registry.promote_champion("CAND_V1", disp1)

        disp2 = PromotionDisposition(
            candidate_id="CAND_V2",
            champion_id=c1.champion_id,
            decision="PROMOTED",
            rationale="V2 pass",
            governor_signature="SIG2",
            timestamp=2000.0,
        )
        c2 = self.registry.promote_champion("CAND_V2", disp2)
        self.assertEqual(self.registry.get_active_champion().champion_id, c2.champion_id)

        # Execute Rollback
        restored = self.registry.rollback_champion(reason="Performance degradation detected", timestamp=2500.0)
        self.assertIsNotNone(restored)
        self.assertEqual(restored.champion_id, c1.champion_id)

        active = self.registry.get_active_champion()
        self.assertIsNotNone(active)
        self.assertEqual(active.champion_id, c1.champion_id)


if __name__ == "__main__":
    unittest.main()
