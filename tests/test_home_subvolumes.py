import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "files/system/usr/libexec/fawos/home-subvolumes"
STEAMAPPS = ".var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps"


def _on_btrfs(path):
    out = subprocess.run(
        ["stat", "-f", "-c", "%T", str(path)], capture_output=True, text=True
    )
    return out.stdout.strip() == "btrfs"


def is_subvolume(path):
    return os.path.isdir(path) and os.stat(path).st_ino == 256


@unittest.skipUnless(
    shutil.which("btrfs") and _on_btrfs(ROOT), "needs btrfs-progs and a btrfs checkout"
)
class HomeSubvolumesTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir=ROOT)
        self.addCleanup(self._cleanup)
        self.home_root = Path(self._tmp.name)

    def _cleanup(self):
        # Unprivileged users cannot rmdir a subvolume that still has content,
        # but empty subvolumes (kernel >= 4.18) are removable like directories.
        self._tmp.cleanup()

    def run_script(self):
        return subprocess.run(
            [str(SCRIPT)],
            capture_output=True,
            text=True,
            timeout=60,
            env={**os.environ, "FAWOS_HOME_ROOT": str(self.home_root)},
        )

    def make_alice(self):
        alice = self.home_root / "alice"
        blob = alice / ".cache/uv/blob"
        blob.parent.mkdir(parents=True)
        blob.write_bytes(b"cache-bytes")
        os.chmod(alice / ".cache", 0o700)
        data = alice / STEAMAPPS / "common/game/data.bin"
        data.parent.mkdir(parents=True)
        data.write_bytes(b"game-bytes")
        return alice

    def test_converts_existing_directories_keeping_contents(self):
        alice = self.make_alice()
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTrue(is_subvolume(alice / ".cache"))
        self.assertTrue(is_subvolume(alice / STEAMAPPS))
        self.assertEqual((alice / ".cache/uv/blob").read_bytes(), b"cache-bytes")
        self.assertEqual(
            (alice / STEAMAPPS / "common/game/data.bin").read_bytes(), b"game-bytes"
        )
        self.assertEqual(os.stat(alice / ".cache").st_mode & 0o777, 0o700)
        self.assertEqual(list(self.home_root.rglob("*.fawos-old")), [])

    def test_creates_missing_targets_only_where_parent_exists(self):
        bob = self.home_root / "bob"
        (bob / ".local/share").mkdir(parents=True)
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        for rel in (".cache", ".cargo", ".rustup", ".local/share/mise", ".local/share/containers"):
            self.assertTrue(is_subvolume(bob / rel), rel)
        self.assertFalse((bob / ".var").exists())

    def test_second_run_is_a_silent_no_op(self):
        self.make_alice()
        self.assertEqual(self.run_script().returncode, 0)
        result = self.run_script()
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_interrupted_leftover_blocks_only_its_own_path(self):
        carol = self.home_root / "carol"
        (carol / ".cache").mkdir(parents=True)
        (carol / ".cache.fawos-old").mkdir()
        result = self.run_script()
        self.assertEqual(result.returncode, 1)
        self.assertFalse(is_subvolume(carol / ".cache"))
        self.assertTrue(is_subvolume(carol / ".cargo"))


if __name__ == "__main__":
    unittest.main()
