import re

with open("tests/are/test_phase5_preflight_invariants.py", "r", encoding="utf-8") as f:
    content = f.read()

# Generate a valid WFOEvidence for testing
wfo_evidence_code = """
        import hashlib, json
        from are.backtest import WFOEvidence, WFOFoldEvidence
        
        f1 = WFOFoldEvidence(1, 0, 100, 101, 105, 106, 200, 2, "sr", {"a":1}, 1.0, None, None, 0, "", {}, {}, (0.01,), 1.0)
        data_dict = {
            "folds": [
                {
                    "winner_params": f1.winner_params,
                    "oos_sharpe": f1.oos_metrics.get("sharpe_ratio", 0.0)
                }
            ],
            "pooled_sharpe": 2.5
        }
        computed_hash = hashlib.sha256(json.dumps(data_dict, sort_keys=True).encode()).hexdigest()
        
        valid_ev = WFOEvidence(
            run_id="test",
            dataset_hash="hash",
            data_start_ts=0,
            data_end_ts=250,
            folds=(f1,),
            fold_count=1,
            parameter_family_size=1,
            evaluation_count=1,
            effective_trial_count=1,
            effective_trial_method="M",
            effective_trial_assumption="A",
            training_overlap_ratio=0.0,
            oos_overlap_ratio=0.0,
            purge_bars=0,
            label_horizon_bars=0,
            label_horizon_unit="BARS",
            warmup_bars=0,
            pooled_oos_returns=tuple([0.01]*1000), 
            pooled_oos_equity=tuple([1.0]*1000),
            pooled_oos_sharpe=2.5,
            pooled_oos_return=0.1,
            pooled_oos_max_drawdown=0.05,
            mean_fold_oos_sharpe=1.0,
            median_fold_oos_sharpe=1.0,
            worst_fold_oos_sharpe=1.0,
            std_fold_oos_sharpe=0.0,
            mean_wfe=1.0,
            median_wfe=1.0,
            worst_wfe=1.0,
            provenance_hash=computed_hash
        )
"""

new_test_5_rigor = """
    def test_checkpoint_5_institutional_rigor_verification(self):
        \"\"\"Checkpoint 5: Strict WFOEvidence consumer.\"\"\"
""" + wfo_evidence_code + """
        res = self.auditor.audit_checkpoint_5_institutional_rigor(wfo_evidence=valid_ev)
        self.assertTrue(res.passed)
        self.assertEqual(res.checkpoint_id, 5)
        self.assertEqual(res.details["gate_status"], "PASS")
"""

start_5_rigor = content.find("def test_checkpoint_5_institutional_rigor_verification")
end_5_rigor = content.find("def test_checkpoint_6_alerting_heartbeat", start_5_rigor)
content = content[:start_5_rigor] + new_test_5_rigor + "\n    " + content[end_5_rigor:]

new_test_full = """
    def test_full_preflight_battery_generates_go_certificate(self):
        \"\"\"Full Battery: 7/7 Checkpoints Passed produces GO disposition with certificate.\"\"\"
        def safe_strategy(df: pl.DataFrame) -> pl.DataFrame:
            return df.with_columns([
                pl.col("price").rolling_mean(window_size=5).alias("ma"),
            ]).with_columns(
                pl.when(pl.col("price") > pl.col("ma"))
                .then(pl.lit(1.0))
                .otherwise(pl.lit(0.0))
                .alias("signal")
            )
            
""" + wfo_evidence_code + """

        report = self.auditor.run_full_preflight_battery(strategy_logic=safe_strategy, wfo_evidence=valid_ev)
        self.assertEqual(report.total_checkpoints, 7)
        self.assertEqual(report.passed_checkpoints, 7)
        self.assertEqual(report.readiness_disposition, "GO")
        self.assertEqual(len(report.certificate_hash), 64)

        # Verify certificate stream was recorded in event store
        rows = self.event_store.fetch_all(
            "SELECT var_ref FROM events WHERE stream_id = ? ORDER BY revision ASC",
            ("governance_certificates",),
        )
        self.assertGreaterEqual(len(rows), 1)
        self.assertEqual(rows[-1][0], report.certificate_hash)
"""

start_full = content.find("def test_full_preflight_battery_generates_go_certificate")
end_full = content.find("def test_full_preflight_battery_fails_closed", start_full)
content = content[:start_full] + new_test_full + "\n    " + content[end_full:]

new_test_5_neg = """
    def test_checkpoint_5_fails_closed_on_negative_sharpe_strategy(self):
        \"\"\"
        REV-01 / WFO-01: Checkpoint 5 WAJIB menolak strategi dengan Sharpe buruk/negatif via WFOEvidence.
        Dilarang menggunakan artificial floor max(1.5, sr).
        \"\"\"
""" + wfo_evidence_code + """
        bad_ev = valid_ev
        import dataclasses
        bad_ev = dataclasses.replace(valid_ev, pooled_oos_sharpe=-1.0)
        
        # We also need to update the hash to not fail integrity check but fail performance check!
        data_dict = {
            "folds": [
                {
                    "winner_params": f1.winner_params,
                    "oos_sharpe": f1.oos_metrics.get("sharpe_ratio", 0.0)
                }
            ],
            "pooled_sharpe": -1.0
        }
        computed_hash = hashlib.sha256(json.dumps(data_dict, sort_keys=True).encode()).hexdigest()
        bad_ev = dataclasses.replace(bad_ev, provenance_hash=computed_hash)
        
        res = self.auditor.audit_checkpoint_5_institutional_rigor(wfo_evidence=bad_ev)
        self.assertFalse(res.passed, "Strategi Sharpe negatif WAJIB gagal di Checkpoint 5")
        self.assertEqual(res.details["gate_status"], "BORDERLINE") # Sharpe < 1.0 fails performance evaluator => BORDERLINE
"""

start_5_neg = content.find("def test_checkpoint_5_fails_closed_on_negative_sharpe_strategy")
end_5_neg = content.find("def test_hourly_stability_harness", start_5_neg)
content = content[:start_5_neg] + new_test_5_neg + "\n    " + content[end_5_neg:]


with open("tests/are/test_phase5_preflight_invariants.py", "w", encoding="utf-8") as f:
    f.write(content)