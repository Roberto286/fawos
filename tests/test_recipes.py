from pathlib import Path
import unittest

try:
    import yaml
except ImportError:  # CI installs it; stdlib-only locally
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
RECIPES = ROOT / "recipes"


def load(name):
    return yaml.safe_load((RECIPES / name).read_text())


def flat_types(name):
    return [m.get("type") or m.get("from-file") for m in load(name)["modules"]]


@unittest.skipUnless(yaml, "PyYAML not installed")
class RecipeSplitTests(unittest.TestCase):
    def test_recipes_parse_and_include_common(self):
        for name in ("recipe.yml", "recipe-desktop.yml"):
            self.assertIn("common.yml", flat_types(name))
        self.assertEqual(load("recipe-desktop.yml")["name"], "fawos-desktop")

    def test_gaming_pieces_only_in_desktop(self):
        self.assertIn("sunshine", (RECIPES / "recipe-desktop.yml").read_text())
        for name in ("recipe.yml", "common.yml"):
            self.assertNotIn("sunshine", (RECIPES / name).read_text())

    def test_initramfs_before_signing_before_systemd_at_the_end(self):
        for name in ("recipe.yml", "recipe-desktop.yml"):
            types = flat_types(name)
            self.assertLess(types.index("initramfs"), types.index("signing"))
            self.assertEqual(types[-2:], ["signing", "systemd"])

    def test_desktop_files_not_in_laptop_recipe(self):
        self.assertNotIn("system-desktop", (RECIPES / "recipe.yml").read_text())
        self.assertIn("system-desktop", (RECIPES / "recipe-desktop.yml").read_text())


if __name__ == "__main__":
    unittest.main()
