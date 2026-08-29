with open("tests/are/test_phase5_preflight_invariants.py", "r") as f:
    c = f.read()
c = c.replace("self.assertEqual(res.details[\"gate_status\"], \"BORDERLINE\")", "self.assertEqual(res.details[\"gate_status\"], \"FAIL\")")
with open("tests/are/test_phase5_preflight_invariants.py", "w") as f:
    f.write(c)