import os
from pathlib import Path
import subprocess
import tempfile
import unittest

DESKTOP = Path(__file__).resolve().parents[1] / "files/system-desktop/usr/libexec/fawos"
TRIGGER = DESKTOP / "gaming-trigger"
UNDO = DESKTOP / "stream-undo"


class TriggerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.calls = self.tmp / "calls"
        (self.tmp / "base.toml").write_text('[default_session]\ncommand = "x"\n')
        (self.tmp / "systemctl").write_text(f'#!/bin/sh\necho "$@" >> {self.calls}\n')
        (self.tmp / "systemctl").chmod(0o755)

    def run_trigger(self, sessions):
        """sessions: list of (id, class). Fake loginctl answers from this table."""
        table = "\n".join(f"{i} {c}" for i, c in sessions)
        (self.tmp / "table").write_text(table + "\n")
        (self.tmp / "loginctl").write_text(
            "#!/bin/sh\n"
            f'if [ "$1" = list-sessions ]; then cut -d" " -f1 {self.tmp}/table; exit; fi\n'
            f'grep "^$2 " {self.tmp}/table | cut -d" " -f2\n'
        )
        (self.tmp / "loginctl").chmod(0o755)
        env = {
            "PATH": "/usr/bin:/bin",
            "FAWOS_LOGINCTL": str(self.tmp / "loginctl"),
            "FAWOS_SYSTEMCTL": str(self.tmp / "systemctl"),
            "FAWOS_GREETD_FLAG": str(self.tmp / "run/flag.toml"),
            "FAWOS_GREETD_DROPIN": str(self.tmp / "run/dropin.conf"),
            "FAWOS_GREETD_BASE": str(self.tmp / "base.toml"),
        }
        return subprocess.run([str(TRIGGER)], env=env, capture_output=True, timeout=10)

    def flag(self):
        return self.tmp / "run/flag.toml"

    def restarts(self):
        return self.calls.read_text().count("restart greetd") if self.calls.exists() else 0

    def test_greeter_only_writes_gaming_config_and_restarts_once(self):
        self.assertEqual(self.run_trigger([("c1", "greeter")]).returncode, 0)
        text = self.flag().read_text()
        self.assertIn('[default_session]', text)
        self.assertIn('[initial_session]', text)
        self.assertIn('user = "gaming"', text)
        self.assertEqual(self.restarts(), 1)
        self.assertIn("stop fawos-gaming-trigger.socket", self.calls.read_text())
        dropin = (self.tmp / "run/dropin.conf").read_text()
        self.assertIn(f"ExecStart=/usr/bin/greetd -c {self.flag()}", dropin)
        self.assertIn("daemon-reload", self.calls.read_text())

    def test_any_user_session_blocks_trigger(self):
        # Class=user covers active, locked and background sessions alike.
        self.run_trigger([("c1", "greeter"), ("2", "user")])
        self.assertFalse(self.flag().exists())
        self.assertEqual(self.restarts(), 0)

    def test_no_greeter_session_blocks_trigger(self):
        self.run_trigger([])
        self.assertFalse(self.flag().exists())
        self.assertEqual(self.restarts(), 0)

    def test_second_poll_does_not_restart_again(self):
        self.run_trigger([("c1", "greeter")])
        self.run_trigger([("c1", "greeter")])
        self.assertEqual(self.restarts(), 1)


class UndoTests(unittest.TestCase):
    def test_undo_powers_off(self):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "sc").write_text(f'#!/bin/sh\necho "$@" > {tmp}/out\n')
        (tmp / "sc").chmod(0o755)
        subprocess.run([str(UNDO)], env={"FAWOS_SYSTEMCTL": str(tmp / "sc")}, timeout=10)
        self.assertEqual((tmp / "out").read_text().strip(), "poweroff")


if __name__ == "__main__":
    unittest.main()
