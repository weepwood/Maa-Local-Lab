import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_mxu", ROOT / "scripts" / "validate_mxu.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class InterfaceTests(unittest.TestCase):
    def test_pi_v2(self):
        module.validate(ROOT, staged=False)

    def test_no_unresolvable_entries(self):
        document = json.loads((ROOT / "interface.json").read_text(encoding="utf-8"))
        pipeline = json.loads((ROOT / "resource" / "pipeline" / "main.json").read_text(encoding="utf-8"))
        self.assertEqual(document["interface_version"], 2)
        self.assertEqual(len(document["task"]), 2)
        self.assertTrue(all(t["entry"] in pipeline for t in document["task"]))
        self.assertEqual(document["pretask"][0]["exec"], "./tools/maa-lab-target.exe")


if __name__ == "__main__":
    unittest.main()
