"""Run deterministic self-checks preserved from the original script."""

from __future__ import annotations

import unittest

from evidence_engine._legacy import (
    deterministic_attachment_linking_tests,
    deterministic_completeness_model_tests,
    deterministic_reporting_pipeline_tests,
)


class LegacySelfCheckTests(unittest.TestCase):
    def test_deterministic_legacy_self_checks_pass(self) -> None:
        checks: dict[str, bool] = {}
        checks.update(deterministic_completeness_model_tests())
        checks.update(deterministic_attachment_linking_tests())
        checks.update(deterministic_reporting_pipeline_tests())

        failed = sorted(name for name, passed in checks.items() if not passed)
        self.assertEqual(failed, [])


if __name__ == "__main__":
    unittest.main()
