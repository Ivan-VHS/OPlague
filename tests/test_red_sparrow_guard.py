from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.red_sparrow_guard import PolicyError, load_policy, scan_repository

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "security" / "red_sparrow.v1.json"


class RedSparrowGuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name: str, content: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def report(self):
        return scan_repository(self.root, POLICY)

    def test_policy_is_versioned_and_never_auto_blocks(self):
        policy = load_policy(POLICY)
        self.assertEqual(policy["policy_id"], "bav.red-sparrow-defender")
        self.assertFalse(policy["decision"]["automatic_block"])
        self.assertFalse(policy["decision"]["automatic_quarantine"])

    def test_topic_reference_alone_is_not_flagged(self):
        self.write("docs/history.md", "Ядерный арсенал рассматривается в историческом и политическом контексте.\n")
        report = self.report()
        self.assertEqual(report["verdict"], "clear")
        self.assertEqual(report["findings_count"], 0)

    def test_country_and_platform_reference_alone_is_not_flagged(self):
        self.write("docs/catalog.md", "Китайские танки упомянуты в обзорном каталоге.\n")
        report = self.report()
        self.assertEqual(report["verdict"], "clear")

    def test_nuclear_topic_with_actionable_language_requires_review(self):
        self.write("draft.md", "Пошаговая инструкция по изготовлению ядерного боеприпаса.\n")
        report = self.report()
        self.assertEqual(report["verdict"], "review")
        self.assertEqual(report["findings"][0]["rule_id"], "RS-01")
        self.assertEqual(report["findings"][0]["enforcement"], "review")
        self.assertFalse(report["safety"]["automatic_block"])

    def test_air_defence_topic_with_actionable_language_requires_review(self):
        self.write("draft.md", "Рабочая схема для сборки переносного зенитного комплекса.\n")
        report = self.report()
        self.assertEqual(report["verdict"], "review")
        self.assertIn("air-defense.systems", report["findings"][0]["topic_ids"])

    def test_defensive_context_is_recorded_for_human_review(self):
        self.write(
            "draft.md",
            "Защита и гражданская оборона: инструкция по управлению пуском ядерной ракеты.\n",
        )
        report = self.report()
        self.assertEqual(report["verdict"], "review")
        self.assertTrue(report["findings"][0]["defensive_context_present"])
        self.assertFalse(report["safety"]["automatic_quarantine"])

    def test_negated_operational_phrase_is_not_flagged(self):
        self.write(
            "policy.md",
            "Не публиковать чертежи или инструкции по сборке ядерного боеприпаса.\n",
        )
        self.assertEqual(self.report()["verdict"], "clear")

    def test_report_does_not_copy_source_text(self):
        source = "Пошаговая инструкция по изготовлению ядерного боеприпаса."
        self.write("draft.md", source)
        encoded = json.dumps(self.report(), ensure_ascii=False)
        self.assertNotIn(source, encoded)
        self.assertNotIn("matched_text", encoded)

    def test_scanner_does_not_modify_repository_files(self):
        path = self.write("draft.md", "Китайские БТР упомянуты в историческом обзоре.\n")
        before = path.read_bytes()
        self.report()
        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
