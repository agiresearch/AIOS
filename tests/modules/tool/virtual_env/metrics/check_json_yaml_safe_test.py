"""
Regression test: ``check_json`` must not execute YAML tags.

``check_json`` in ``aios/tool/virtual_env/evaluators/metrics/general.py``
used to read YAML results with ``yaml.load(f, Loader=yaml.Loader)``, which
honors ``!!python/...`` tags and runs them while parsing. A benign file
must still be scored, and a file with a Python tag must not run.

No network, no external service: the files are in a temporary directory and
the only side effect checked is a marker file the hostile tag would create.
"""
import os
import tempfile
import unittest

import yaml

from aios.tool.virtual_env.evaluators.metrics.general import check_json


class CheckJsonYamlSafeTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="aios-yaml-")
        self.base = self._tmp.name
        self.marker = os.path.join(self.base, "marker.txt")
        self.hostile = os.path.join(self.base, "hostile.yaml")
        with open(self.hostile, "w", encoding="utf-8") as handle:
            handle.write(
                "!!python/object/apply:os.system ['echo PWNED > \"%s\"']\n"
                % self.marker.replace("\\", "/")
            )

    def tearDown(self):
        self._tmp.cleanup()

    def test_benign_yaml_still_parses(self):
        benign = os.path.join(self.base, "benign.yaml")
        with open(benign, "w", encoding="utf-8") as handle:
            handle.write("key: value\n")
        self.assertEqual(check_json(benign, {"expect": [], "unexpect": []}, is_yaml=True), 1.0)

    def test_python_object_tag_is_not_executed(self):
        try:
            check_json(self.hostile, {"expect": [], "unexpect": []}, is_yaml=True)
        except yaml.YAMLError:
            pass
        self.assertFalse(os.path.exists(self.marker),
                         "the python/object/apply tag executed code")


if __name__ == "__main__":
    unittest.main(verbosity=2)
