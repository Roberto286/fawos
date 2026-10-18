import os
from pathlib import Path
import subprocess
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "files/system/usr/bin/fawos-update"


class UpdateSafetyTests(unittest.TestCase):
    @unittest.skipUnless(os.geteuid() == 0, "requires root to exercise sudo invocation")
    def test_root_is_rejected_even_with_sudo_user(self):
        result = subprocess.run(
            [str(SCRIPT)],
            env={"PATH": "/nonexistent", "SUDO_USER": "desktop"},
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 2)

    def test_missing_update_commands_fail(self):
        identity = (
            {"user": 65534, "group": 65534, "extra_groups": []}
            if os.geteuid() == 0
            else {}
        )
        result = subprocess.run(
            [str(SCRIPT)],
            env={"PATH": "/nonexistent"},
            capture_output=True,
            timeout=10,
            **identity,
        )
        self.assertEqual(result.returncode, 1)

    def test_unknown_arguments_are_rejected(self):
        result = subprocess.run(
            [str(SCRIPT), "--unsupported"],
            env={"PATH": "/nonexistent"},
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
