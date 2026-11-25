import os
from pathlib import Path
import subprocess
import tempfile
import time
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

FAKE_FLATPAK = """#!/usr/bin/bash
case $1 in
    list) if [[ " $* " == *" --user "* ]]; then printf 'org.test.App\\t%s\\tflathub\\n' "$ACTIVE"; fi ;;
    remote-info) cat "$REMOTE_LOG" ;;
    update) echo "$*" >> "$UPDATES" ;;
esac
"""


def commit_log(*days_ago):
    """`flatpak remote-info --log` output: one (hash, date) block per age, newest first."""
    out = []
    for i, days in enumerate(days_ago):
        date = time.strftime("%Y-%m-%d 12:00:00 +0000", time.gmtime(time.time() - days * 86400))
        out.append(f"        Commit: {str(i) * 64}\n       Subject: Export\n          Date: {date}\n")
    return "\n".join(out)


@unittest.skipIf(os.geteuid() == 0, "script refuses to run as root")
class FlatpakDelayTests(unittest.TestCase):
    def run_flatpak_step(self, installed_index):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "flatpak").write_text(FAKE_FLATPAK)
            (tmp / "sudo").write_text('#!/usr/bin/bash\nexec "$@"\n')
            for name in ("flatpak", "sudo"):
                (tmp / name).chmod(0o755)
            (tmp / "log").write_text(commit_log(1, 10, 20))
            env = {
                "PATH": f"{tmp}:/usr/bin",
                "REMOTE_LOG": str(tmp / "log"),
                "UPDATES": str(tmp / "updates"),
                "ACTIVE": str(installed_index) * 12,
            }
            subprocess.run([str(SCRIPT), "flatpak"], env=env, capture_output=True, timeout=10, check=True)
            updates = tmp / "updates"
            return updates.read_text() if updates.exists() else ""

    def test_updates_to_newest_commit_older_than_a_week(self):
        # Installed commit is the 20-day-old one; 1-day-old is too fresh, 10-day-old is the target.
        self.assertIn("--commit=" + "1" * 64, self.run_flatpak_step(2))

    def test_keeps_installed_commit_that_is_newer_than_the_target(self):
        self.assertEqual(self.run_flatpak_step(0), "")
        self.assertEqual(self.run_flatpak_step(1), "")


if __name__ == "__main__":
    unittest.main()
