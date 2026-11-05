import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "files/system/usr/libexec/fawos/normalize-home"
UNIT = ROOT / "files/system/etc/systemd/system/fawos-normalize-home.service"
RECIPE = ROOT / "recipes/recipe.yml"


class NormalizeHomeTests(unittest.TestCase):
    def test_script_is_executable_and_valid_bash(self):
        self.assertTrue(SCRIPT.is_file())
        self.assertTrue(SCRIPT.stat().st_mode & 0o111)
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True, timeout=10)

    def test_script_skips_when_home_is_not_a_symlink(self):
        source = SCRIPT.read_text()
        self.assertIn("/var/home", source)
        self.assertIn("readlink -f /home", source)

    def test_unit_runs_before_greetd(self):
        unit = UNIT.read_text()
        self.assertIn("ExecStart=/usr/libexec/fawos/normalize-home", unit)
        self.assertIn("ConditionPathIsSymbolicLink=/home", unit)
        self.assertIn("Before=greetd.service", unit)

    def test_unit_is_enabled_in_recipe(self):
        self.assertIn("- fawos-normalize-home.service", RECIPE.read_text())


if __name__ == "__main__":
    unittest.main()
