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


@unittest.skipUnless(yaml, "PyYAML not installed")
class AutoUpdateTests(unittest.TestCase):
    """Stock updaters bypass fawos-update's 7-day hold, so they must stay off."""

    def test_stock_auto_updaters_disabled_and_notifier_enabled(self):
        for name in ("recipe.yml", "recipe-desktop.yml"):
            m = [m for m in load(name)["modules"] if m.get("type") == "systemd"][-1]
            self.assertTrue(
                {"bootc-fetch-apply-updates.timer", "flatpak-system-updates.timer"}
                <= set(m["system"]["disabled"]),
                name,
            )
            self.assertIn("flatpak-user-updates.timer", m["user"]["disabled"], name)
            self.assertIn("fawos-update-notify.service", m["user"]["enabled"], name)


@unittest.skipUnless(yaml, "PyYAML not installed")
class LocalSendTests(unittest.TestCase):
    """LocalSend must be installed everywhere *and* reachable from a phone.

    Inbound 53317 is what makes phone → PC work; PC → phone only uses outgoing
    traffic, so dropping the ports fails one direction and looks like an app bug.
    """

    def test_installed_in_both_images(self):
        for name in ("recipe.yml", "recipe-desktop.yml"):
            flatpaks = [
                p
                for m in load(name)["modules"]
                if m.get("type") == "default-flatpaks"
                for c in m["configurations"]
                for p in c.get("install", [])
            ]
            self.assertIn("org.localsend.localsend_app", flatpaks, name)

    def test_inbound_ports_open_in_public_zone(self):
        import xml.etree.ElementTree as ET

        zone = ET.parse(ROOT / "files/system/etc/firewalld/zones/public.xml").getroot()
        ports = {(p.get("port"), p.get("protocol")) for p in zone.iter("port")}
        self.assertTrue({("53317", "tcp"), ("53317", "udp")} <= ports, ports)
        # The zone file replaces the stock one, so the defaults must survive.
        services = {s.get("name") for s in zone.iter("service")}
        self.assertTrue({"ssh", "mdns", "dhcpv6-client"} <= services, services)


if __name__ == "__main__":
    unittest.main()
