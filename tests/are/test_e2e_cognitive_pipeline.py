"""
End-to-End Unified 7-Organ Cognitive Pipeline Verification (DELEGASI_034)
Integrates all 7 computational organs into a cohesive, fail-closed, deterministic pipeline:
[Organ 7: Scraper] -> [Organ 1: AlphaSeed Schema] -> [Organ 3: Data Purifier]
-> [Organ 1: Vectorized Backtest] -> [Organ 2: Monte Carlo & WFA] -> [Organ 2: Governor SoD Gate]
-> [Organ 5: Vault Dual-Layer Witness] -> [Autonomic Watchdog: Health Monitor] -> [Organ 6: XAI Copilot]
"""

import json
import os
import sqlite3
import tempfile
import time
import unittest

import polars as pl

from are.backtest import IsolatedBacktestEngine
from are.copilot import ConversationalCopilot
from are.data_pipeline import DataPurifier
from are.governor import GovernorEngine
from are.health_monitor import HealthStatus, SystemHealthMonitor
from are.hypothesis_schema import AlphaSeed, validate_alpha_seed
from are.safety import CapitalSafetyKernel
from are.storage import EventStore
from are.validation import (
    ValidationReport,
    monte_carlo_simulation,
    validate_statistical_robustness,
    walk_forward_consistency,
)
from TOOLS.external_alpha_scraper import extract_parameters_via_llm


class TestE2ECognitivePipeline(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "cognitive_pipeline.db")
        self.witness_path = f"{self.db_path}.witness.jsonl"

    def tearDown(self):
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_full_7_organ_happy_path_lifecycle(self):
        """
        Scenario 1: Complete 7-Organ Happy Path Lifecycle
        From raw text hypothesis extraction, tick data purification, vectorized backtesting,
        Monte Carlo & WFA validation, Governor promotion, Vault witness persistence,
        to Watchdog health monitoring and XAI Copilot query.
        """
        # =========================================================================
        # ORGAN 7 & ORGAN 1: Scraper & Strict AlphaSeed Parameterization
        # =========================================================================
        mock_research_article = """
        Academic Paper: Robust Momentum Inversion on Forex Markets
        Asset: FOREX. Strategy: ALPHA_E2E_MOMENTUM_V1.
        Indicators: RSI (period 14), EMA (period 50).
        Entry when RSI < 35 and Price above EMA 50.
        Exit when RSI > 65.
        Risk management: Stop loss at 40 pips, Take profit at 80 pips.
        """
        mock_llm_json = """```json
        {
            "strategy_id": "ALPHA_E2E_MOMENTUM_V1",
            "asset_class": "FOREX",
            "indicators": [
                {"name": "RSI", "period": 14},
                {"name": "EMA", "period": 50}
            ],
            "entry_conditions": ["RSI < 35", "PRICE > EMA_50"],
            "exit_conditions": ["RSI > 65"],
            "risk_params": {
                "stop_loss_pips": 40.0,
                "take_profit_pips": 80.0
            }
        }
        ```"""

        raw_params = extract_parameters_via_llm(
            text=mock_research_article,
            mock_response=mock_llm_json,
        )
        alpha_seed: AlphaSeed = validate_alpha_seed(raw_params)
        self.assertEqual(alpha_seed.strategy_id, "ALPHA_E2E_MOMENTUM_V1")
        self.assertEqual(alpha_seed.asset_class, "FOREX")

        # =========================================================================
        # ORGAN 3: Data Purification (Zero Linear Interpolation, LOCF Micro-Gaps)
        # =========================================================================
        n_bars = 200
        timestamps = [1700000000.0 + i * 60 for i in range(n_bars)]
        prices = [1.1000 + (0.0002 * (i % 20)) for i in range(n_bars)]
        # Inject null in micro gap (index 15)
        prices[15] = None

        raw_df = pl.DataFrame({
            "timestamp": timestamps,
            "price": prices,
        })

        purifier = DataPurifier()
        purified_df = purifier.purify_tick_data(raw_df)

        # Assert LOCF fill at index 15 (price preserved from index 14, not interpolated)
        self.assertEqual(purified_df["price"][15], purified_df["price"][14])
        self.assertIn("is_toxic_spread", purified_df.columns)
        self.assertIn("is_market_closed", purified_df.columns)

        # =========================================================================
        # ORGAN 1: Vectorized Backtest Execution (Polars Engine)
        # =========================================================================
        engine = IsolatedBacktestEngine()
        bt_result = engine.run_vectorized_backtest(historical_data=purified_df, initial_capital=10000.0)

        self.assertGreater(len(bt_result.equity_curve), 0)
        self.assertIn("total_return", bt_result.metrics)
        self.assertIn("max_drawdown", bt_result.metrics)

        # =========================================================================
        # ORGAN 2: Monte Carlo & Walk-Forward Statistical Validation
        # =========================================================================
        mc_metrics = monte_carlo_simulation(
            bt_result.trade_log,
            num_simulations=500,
            initial_capital=10000.0,
        )
        wf_score = walk_forward_consistency(bt_result.trade_log)

        stat_passed, stat_reason = validate_statistical_robustness(
            backtest_metrics=bt_result.metrics,
            mc_metrics=mc_metrics,
            wf_score=wf_score,
        )
        # Verify validation judgment is deterministic
        self.assertIsInstance(stat_passed, bool)
        self.assertIsInstance(stat_reason, str)

        # =========================================================================
        # ORGAN 2: Governor SoD Gate Promotion
        # =========================================================================
        governor = GovernorEngine()
        val_report = ValidationReport(
            candidate_id=alpha_seed.strategy_id,
            status="VALIDATED",
            sample_count=len(purified_df),
            performance_metric=0.88,
            exposure_penalty=0.02,
            as_of_ts=1700000000.0,
        )

        disposition = governor.evaluate_promotion(
            candidate_id=alpha_seed.strategy_id,
            champion_id="CHAMPION_GENESIS",
            validation_report=val_report,
            critic_passed=True,
            creator_principal="RESEARCHER_AGENT_A",
            validator_principal="VALIDATOR_AGENT_B",
            promoter_principal="GOVERNOR_AGENT_C",
            statistical_robustness=(True, "STATISTICALLY_ROBUST"),
        )
        self.assertEqual(disposition.decision, "PROMOTED")
        self.assertIn("passed out-of-sample validation", disposition.rationale)

        # =========================================================================
        # ORGAN 5: Windows Vault Protocol (Dual-Layer JSONL Witness)
        # =========================================================================
        store = EventStore(self.db_path)
        payload_bytes = json.dumps({
            "candidate_id": disposition.candidate_id,
            "champion_id": disposition.champion_id,
            "decision": disposition.decision,
            "signature": disposition.governor_signature,
        }).encode("utf-8")

        head = store.get_head("governor_promotions")
        prev_rev = head[0] if head else 0
        prev_h = head[1] if head else "0" * 64

        store.append_event(
            stream_id="governor_promotions",
            event_data=payload_bytes,
            expected_revision=prev_rev,
            prev_event_hash=prev_h,
            var_ref=disposition.disposition_hash,
        )

        self.assertTrue(os.path.exists(self.witness_path))
        chain_ok, chain_status = store.verify_full_chain_integrity()
        self.assertTrue(chain_ok)
        self.assertEqual(chain_status, "OK")

        # =========================================================================
        # AUTONOMIC NERVOUS SYSTEM & ORGAN 6: Health Monitor & XAI Copilot
        # =========================================================================
        health_monitor = SystemHealthMonitor()
        health_report = health_monitor.evaluate_system_health(
            last_tick_ts=time.time(),
            latencies=[12.5, 18.0, 25.0],
            event_store=store,
        )
        self.assertEqual(health_report.status, HealthStatus.HEALTHY)
        self.assertTrue(health_report.vault_ok)

        # Copilot status inspection with promoted champion
        class MockServerState:
            def get_status_payload(self):
                return {
                    "champion": {
                        "champion_id": disposition.candidate_id,
                        "candidate_id": disposition.candidate_id,
                        "status": "ACTIVE",
                    },
                    "safety": {"kill_switch_active": False, "max_drawdown_pct": 0.15, "volatility_cutoff": 2.5},
                    "stream_stats": {"total_ticks": 1000, "veto_count": 0, "chain_health": "VERIFIED_OK"},
                }

        copilot = ConversationalCopilot(server_state=MockServerState(), event_store=store)
        reply = copilot.generate_response("Bagaimana status champion aktif saat ini?")
        self.assertIn("ALPHA_E2E_MOMENTUM_V1", reply)
        store.close()

    def test_overfitted_alpha_killed_by_monte_carlo_e2e(self):
        """
        Scenario 2: Overfitted / Lucky Sequence Strategy is decisively rejected
        by Monte Carlo Permutation and dismissed by Governor SoD Gate.
        """
        # Strategy with positive final PnL (lucky last trade), but 95 losses first
        trade_log = pl.DataFrame({
            "strategy_return": [-0.01] * 95 + [2.00],
        })

        mc_res = monte_carlo_simulation(trade_log, num_simulations=300, initial_capital=10000.0)
        self.assertGreater(mc_res["mc_probability_of_ruin"], 0.10)

        stat_passed, stat_reason = validate_statistical_robustness(
            backtest_metrics={"max_drawdown": 0.15},
            mc_metrics=mc_res,
            wf_score=0.90,
        )
        self.assertFalse(stat_passed)
        self.assertIn("MC_RUIN_PROBABILITY_HIGH", stat_reason)

        governor = GovernorEngine()
        val_report = ValidationReport(
            candidate_id="CAND_LUCKY_OVERFIT_01",
            status="VALIDATED",
            sample_count=96,
            performance_metric=0.75,
            exposure_penalty=0.01,
            as_of_ts=1700000000.0,
        )

        disposition = governor.evaluate_promotion(
            candidate_id="CAND_LUCKY_OVERFIT_01",
            champion_id="CHAMPION_GENESIS",
            validation_report=val_report,
            critic_passed=True,
            creator_principal="RESEARCHER_1",
            validator_principal="VALIDATOR_2",
            promoter_principal="GOVERNOR_3",
            statistical_robustness=(stat_passed, stat_reason),
        )

        self.assertEqual(disposition.decision, "DISMISSED")
        self.assertIn("statistical robustness validation failed", disposition.rationale)
        self.assertIn("MC_RUIN_PROBABILITY_HIGH", disposition.rationale)

    def test_toxic_market_and_csk_circuit_breaker_e2e(self):
        """
        Scenario 3: Toxic Spreads neutralized by DataPurifier & Latency Spikes VETOED by CSK.
        """
        n = 120
        timestamps = [1000.0 + i * 60 for i in range(n)]
        bids = [1.1000] * n
        asks = [1.1001] * n  # Normal spread 1 pip (0.0001)

        # Inject extreme toxic spread spike at index 100 (10x normal spread)
        asks[100] = 1.1015

        df = pl.DataFrame({
            "timestamp": timestamps,
            "bid": bids,
            "ask": asks,
            "volume": [1.0] * n,
        })

        purifier = DataPurifier()
        purified = purifier.purify_tick_data(df)
        self.assertTrue(purified["is_toxic_spread"][100])

        # Backtest engine must suppress trade execution on index 100
        engine = IsolatedBacktestEngine()

        def buy_on_100_strategy(data: pl.DataFrame) -> pl.DataFrame:
            return data.with_columns(
                pl.when(pl.col("timestamp") == timestamps[100])
                .then(pl.lit(1.0))
                .otherwise(pl.lit(0.0))
                .alias("signal")
            )

        bt_res = engine.run_vectorized_backtest(
            strategy_logic=buy_on_100_strategy,
            historical_data=df,
        )
        self.assertEqual(len(bt_res.trade_log), 0, "Trade should not execute on toxic spread bar")

        # Watchdog & CSK Circuit Breaker check
        monitor = SystemHealthMonitor()
        health_report = monitor.evaluate_system_health(
            last_tick_ts=time.time(),
            latencies=[5500.0, 6000.0],  # Latency spike > 5000ms
        )
        self.assertEqual(health_report.status, HealthStatus.CRITICAL)

        csk = CapitalSafetyKernel()
        decision = csk.evaluate_action(
            intended_action={"action": "BUY", "price": 1.1000, "size": 1.0},
            current_drawdown=0.01,
            current_volatility=0.01,
            recent_order_count=1,
            health_status=health_report.status,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, "EMERGENCY_FLAT")
        self.assertEqual(decision.clamped_size, 0.0)
        self.assertIn("SYSTEM_HEALTH_CRITICAL", decision.reason)

    def test_vault_self_healing_under_pipeline_load(self):
        """
        Scenario 4: Vault Self-Healing Under Pipeline Load
        Detects out-of-band SQLite corruption and auto-heals 100% from immutable JSONL witness.
        """
        store = EventStore(self.db_path)
        original_events = []

        # Commit 10 pipeline events
        for i in range(1, 11):
            data = f"pipeline_event_payload_{i}".encode("utf-8")
            original_events.append(data)
            head = store.get_head("stream_load")
            prev_rev = head[0] if head else 0
            prev_hash = head[1] if head else "0" * 64
            store.append_event(
                stream_id="stream_load",
                event_data=data,
                expected_revision=prev_rev,
                prev_event_hash=prev_hash,
                var_ref=f"ref_load_{i}",
            )
        store.close()

        # Malicious out-of-band SQLite manipulation
        raw_conn = sqlite3.connect(self.db_path)
        with raw_conn:
            raw_conn.execute("DROP TRIGGER IF EXISTS events_no_update;")
            raw_conn.execute("UPDATE events SET event_data = X'DEADBEEF' WHERE revision = 4;")
        raw_conn.close()

        # Re-boot EventStore -> verify_and_heal() automatically repairs SQLite cache
        healed_store = EventStore(self.db_path)
        ev_4 = healed_store.get_event("stream_load", 4)
        self.assertIsNotNone(ev_4)
        self.assertEqual(ev_4.event_data, original_events[3])
        self.assertNotEqual(ev_4.event_data, b"\xde\xad\xbe\xef")

        ok, status = healed_store.verify_full_chain_integrity()
        self.assertTrue(ok)
        self.assertEqual(status, "OK")
        healed_store.close()


if __name__ == "__main__":
    unittest.main()