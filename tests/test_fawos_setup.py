import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "files/system/usr/bin/fawos-setup"


class SetupTests(unittest.TestCase):
    def test_unknown_arguments_are_rejected(self):
        result = subprocess.run(
            [str(SCRIPT), "--x"],
            env={"PATH": "/nonexistent"},
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 2)

    @unittest.skipUnless(os.geteuid() == 0, "requires root")
    def test_root_is_rejected(self):
        result = subprocess.run(
            [str(SCRIPT)],
            env={"PATH": "/usr/bin:/bin"},
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 2)

    @unittest.skipIf(os.geteuid() == 0, "root is rejected by the script")
    def test_eof_skips_every_step_and_writes_marker(self):
        with tempfile.TemporaryDirectory() as home:
            result = subprocess.run(
                [str(SCRIPT)],
                env={
                    "HOME": home,
                    "PATH": "/usr/bin:/bin",
                },
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(
                (Path(home) / ".local/state/fawos/setup-done").exists()
            )
            self.assertFalse((Path(home) / ".ssh/id_ed25519").exists())


if __name__ == "__main__":
    unittest.main()
