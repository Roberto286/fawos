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
    list)
        if [[ " $* " == *" --user "* ]]; then
            if [[ " $* " == *" --app "* ]]; then
                printf 'org.test.App/x86_64/stable\\t%s\\tflathub\\n' "${ACTIVE:0:12}"
            elif [[ " $* " == *" --runtime "* ]]; then
                printf 'org.test.Platform/x86_64/1\\t%s\\tflathub\\n' "${ACTIVE:0:12}"
            fi
        fi ;;
    remote-info)
        if [[ " $* " == *" --log "* ]]; then cat "$REMOTE_LOG"; else echo '       Runtime: org.test.Platform/x86_64/1'; fi ;;
    info) if [[ " $* " == *" --show-commit "* ]]; then echo "$ACTIVE"; fi ;;
    update)
        echo "$*" >> "$UPDATES"
        [[ -z ${FAIL_ON-} || " $* " != *" $FAIL_ON "* ]] || exit 1 ;;
esac
exit 0
"""

FAKE_SUDO = """#!/usr/bin/bash
while [[ ${1-} == -* ]]; do shift; done
(( $# )) || exit 0
exec "$@"
"""


def commit_log(*days_ago):
    """`flatpak remote-info --log` output: one (hash, date) block per age, newest first."""
    out = []
    for i, days in enumerate(days_ago):
        date = time.strftime("%Y-%m-%d 12:00:00 +0000", time.gmtime(time.time() - days * 86400))
        out.append(f"        Commit: {str(i) * 64}\n       Subject: Export\n          Date: {date}\n")
    return "\n".join(out)


def install_fakes(tmp, fakes):
    for name, body in fakes.items():
        (tmp / name).write_text(body)
        (tmp / name).chmod(0o755)


@unittest.skipIf(os.geteuid() == 0, "script refuses to run as root")
class FlatpakDelayTests(unittest.TestCase):
    def run_flatpak_step(self, installed_index, args=("flatpak",), **extra_env):
        """Returns (returncode, stdout, text of every `flatpak update` call)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            install_fakes(tmp, {"flatpak": FAKE_FLATPAK, "sudo": FAKE_SUDO, "snapper": "#!/usr/bin/bash\necho 42\n"})
            (tmp / "log").write_text(commit_log(1, 10, 20))
            env = {
                "PATH": f"{tmp}:/usr/bin",
                "REMOTE_LOG": str(tmp / "log"),
                "UPDATES": str(tmp / "updates"),
                "ACTIVE": str(installed_index) * 64,
                **extra_env,
            }
            result = subprocess.run([str(SCRIPT), *args], env=env, capture_output=True, text=True, timeout=20)
            updates = tmp / "updates"
            return result.returncode, result.stdout, updates.read_text() if updates.exists() else ""

    def test_apps_and_runtimes_move_to_newest_commit_older_than_a_week(self):
        # Installed commit is the 20-day-old one; 1-day-old is too fresh, 10-day-old is the target.
        rc, _, updates = self.run_flatpak_step(2)
        self.assertEqual(rc, 0)
        for ref in ("app/org.test.App/x86_64/stable", "runtime/org.test.Platform/x86_64/1"):
            lines = [l for l in updates.splitlines() if l.endswith(ref) and "--no-pull" in l]
            self.assertEqual(len(lines), 1, (ref, updates))
            self.assertIn("--commit=" + "1" * 64, lines[0])
        # --no-deps keeps an app from dragging its runtime to the newest commit.
        for line in updates.splitlines():
            self.assertIn("--no-deps", line)

    def test_keeps_installed_commit_that_is_newer_than_the_target(self):
        for index in (0, 1):
            rc, _, updates = self.run_flatpak_step(index)
            self.assertEqual((rc, updates), (0, ""))

    def test_failed_download_applies_nothing(self):
        rc, _, updates = self.run_flatpak_step(2, FAIL_ON="--no-deploy")
        self.assertEqual(rc, 1)
        self.assertNotIn("--no-pull", updates)

    def test_failed_apply_rolls_back_to_previous_commit(self):
        rc, _, updates = self.run_flatpak_step(2, FAIL_ON="--no-pull")
        self.assertEqual(rc, 1)
        rollbacks = [l for l in updates.splitlines() if "--no-pull" not in l and "--no-deploy" not in l]
        self.assertTrue(any("--commit=" + "2" * 64 in l for l in rollbacks), updates)

    def test_check_reports_pending_with_exit_100(self):
        rc, out, updates = self.run_flatpak_step(2, args=("--check", "flatpak"))
        self.assertEqual(rc, 100)
        self.assertIn("org.test.App", out)
        self.assertEqual(updates, "")
        rc, _, updates = self.run_flatpak_step(0, args=("--check", "flatpak"))
        self.assertEqual((rc, updates), (0, ""))


@unittest.skipIf(os.geteuid() == 0, "script refuses to run as root")
class ImageDelayTests(unittest.TestCase):
    def test_target_is_newest_release_from_a_whole_day_before_the_cutoff(self):
        def day(n):
            return time.strftime("%Y%m%d", time.gmtime(time.time() - n * 86400))

        d6, d7, d8 = day(6), day(7), day(8)
        fakes = {
            "rpm-ostree": '#!/usr/bin/bash\necho \'{"deployments":[{"booted":true,'
            '"container-image-reference":"ostree-image-signed:docker://ghcr.io/x/fawos:latest","timestamp":0}]}\'\n',
            "skopeo": f'#!/usr/bin/bash\necho \'{{"Tags":["{d6}","{d7}","{d8}","latest"]}}\'\n',
        }
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            install_fakes(tmp, fakes)
            result = subprocess.run(
                [str(SCRIPT), "--check", "image"],
                env={"PATH": f"{tmp}:/usr/bin"},
                capture_output=True,
                text=True,
                timeout=20,
            )
        self.assertEqual(result.returncode, 100, result.stderr)
        line = next(l for l in result.stdout.splitlines() if l.startswith("image:"))
        self.assertEqual(line, f"image: 19700101 -> {d8}")
        self.assertNotIn(d7, line)

    def test_force_takes_the_newest_release(self):
        today = time.strftime("%Y%m%d", time.gmtime())
        fakes = {
            "rpm-ostree": '#!/usr/bin/bash\necho \'{"deployments":[{"booted":true,'
            '"container-image-reference":"ostree-image-signed:docker://ghcr.io/x/fawos:latest","timestamp":0}]}\'\n',
            "skopeo": f'#!/usr/bin/bash\necho \'{{"Tags":["{today}","latest"]}}\'\n',
        }
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            install_fakes(tmp, fakes)
            env = {"PATH": f"{tmp}:/usr/bin"}
            held = subprocess.run([str(SCRIPT), "--check", "image"], env=env, capture_output=True, text=True, timeout=20)
            forced = subprocess.run([str(SCRIPT), "--check", "--force", "image"], env=env, capture_output=True, text=True, timeout=20)
        self.assertEqual(held.returncode, 0)
        self.assertEqual(forced.returncode, 100, forced.stderr)
        self.assertIn(f"image: 19700101 -> {today}", forced.stdout)


if __name__ == "__main__":
    unittest.main()
