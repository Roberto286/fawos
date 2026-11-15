from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "files/system/usr/libexec/fawos/power-profile"
UNIT = ROOT / "files/system/etc/systemd/system/fawos-power-profile.service"
RULE = ROOT / "files/system/usr/lib/udev/rules.d/70-fawos-power-profile.rules"

GET = '#!/bin/sh\ncase "$1" in\n  get) cat "$FAWOS_FAKE_STATE" ;;\n  set) echo "set $2" >> "$FAWOS_FAKE_LOG"\n'
SET_OK = 'echo "$2" > "$FAWOS_FAKE_STATE";;\nesac\n'
SET_FAIL = 'exit 1;;\nesac\n'


class PowerProfileTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.sys = self.tmp / "sys"
        (self.sys / "class/power_supply").mkdir(parents=True)
        self.cpufreq = self.sys / "devices/system/cpu/cpufreq"
        self.cpufreq.mkdir(parents=True)
        self.log = self.tmp / "log"
        self.state = self.tmp / "state"
        self.state.write_text("")

    def supply(self, name, type_, **values):
        path = self.sys / "class/power_supply" / name
        path.mkdir()
        (path / "type").write_text(type_ + "\n")
        for key, value in values.items():
            (path / key).write_text(f"{value}\n")

    def policy(self, cpu):
        path = self.cpufreq / f"policy{cpu}"
        path.mkdir()
        for name in ("scaling_governor", "energy_performance_preference",
                     "scaling_min_freq", "boost",
                     "amd_pstate_lowest_nonlinear_freq", "cpuinfo_min_freq"):
            (path / name).write_text("x\n")
        (path / "amd_pstate_lowest_nonlinear_freq").write_text("1972728")
        (path / "cpuinfo_min_freq").write_text("550000")
        return path

    def run_script(self, set_succeeds=True):
        fake = self.tmp / "powerprofilesctl"
        fake.write_text(GET + (SET_OK if set_succeeds else SET_FAIL))
        fake.chmod(0o755)
        env = {
            "PATH": "/usr/bin:/bin",
            "FAWOS_SYSFS": str(self.sys),
            "FAWOS_POWERPROFILESCTL": str(fake),
            "FAWOS_FAKE_LOG": str(self.log),
            "FAWOS_FAKE_STATE": str(self.state),
        }
        return subprocess.run([str(SCRIPT)], env=env, capture_output=True, timeout=10)

    def sets(self):
        if not self.log.exists():
            return []
        return self.log.read_text().split("\n")[:-1]

    def test_desktop_without_battery_is_performance(self):
        self.supply("AC", "Mains", online=1)
        self.assertEqual(self.run_script().returncode, 0)
        self.assertEqual(self.sets(), ["set performance"])

    def test_laptop_on_ac_is_performance(self):
        self.supply("AC", "Mains", online=1)
        self.supply("BAT0", "Battery", capacity=10)
        self.run_script()
        self.assertEqual(self.sets(), ["set performance"])

    def test_laptop_on_battery_above_threshold_is_balanced(self):
        self.supply("AC", "Mains", online=0)
        self.supply("BAT0", "Battery", capacity=80)
        self.run_script()
        self.assertEqual(self.sets(), ["set balanced"])

    def test_laptop_on_battery_at_threshold_stays_balanced(self):
        self.supply("AC", "Mains", online=0)
        self.supply("BAT0", "Battery", capacity=50)
        self.run_script()
        self.assertEqual(self.sets(), ["set balanced"])

    def test_laptop_on_battery_below_threshold_is_power_saver(self):
        self.supply("AC", "Mains", online=0)
        self.supply("BAT0", "Battery", capacity=49)
        self.run_script()
        self.assertEqual(self.sets(), ["set power-saver"])

    def test_average_of_several_batteries(self):
        self.supply("AC", "Mains", online=0)
        self.supply("BAT0", "Battery", capacity=100)
        self.supply("BAT1", "Battery", capacity=0)
        self.run_script()
        self.assertEqual(self.sets(), ["set balanced"])

    def test_usb_c_charger_counts_as_ac(self):
        self.supply("UC0", "USB", online=1)
        self.supply("BAT0", "Battery", capacity=20)
        self.run_script()
        self.assertEqual(self.sets(), ["set performance"])

    def test_no_daemon_call_when_profile_already_matches(self):
        self.state.write_text("balanced\n")
        self.supply("AC", "Mains", online=0)
        self.supply("BAT0", "Battery", capacity=80)
        self.run_script()
        self.assertEqual(self.sets(), [])

    def test_falls_back_to_cpufreq_when_daemon_refuses(self):
        self.supply("AC", "Mains", online=1)
        policy = self.policy(0)
        self.assertEqual(self.run_script(set_succeeds=False).returncode, 0)
        self.assertEqual(self.sets(), ["set performance"])
        self.assertEqual((policy / "scaling_governor").read_text(), "performance")
        self.assertEqual((policy / "energy_performance_preference").read_text(), "performance")
        self.assertEqual((policy / "boost").read_text(), "1")
        self.assertEqual((policy / "scaling_min_freq").read_text(), "1972728")

    def test_one_unwritable_policy_does_not_abort_the_fallback(self):
        self.supply("AC", "Mains", online=0)
        self.supply("BAT0", "Battery", capacity=10)
        good = self.policy(0)
        bad = self.policy(1)
        # A directory where the boost file should be: every write fails.
        (bad / "boost").unlink()
        (bad / "boost").mkdir()
        self.assertEqual(self.run_script(set_succeeds=False).returncode, 0)
        self.assertEqual((good / "scaling_governor").read_text(), "powersave")
        self.assertEqual((good / "energy_performance_preference").read_text(), "power")
        self.assertEqual((good / "boost").read_text(), "0")
        self.assertEqual((good / "scaling_min_freq").read_text(), "550000")


class UnitTests(unittest.TestCase):
    def test_unit_avoids_the_multi_user_ordering_cycle(self):
        text = UNIT.read_text()
        # power-profiles-daemon is After=multi-user.target; being pulled in by
        # multi-user.target as well would recreate the cycle that silently
        # dropped the old unit.
        self.assertIn("WantedBy=graphical.target", text)
        self.assertIn("After=power-profiles-daemon.service", text)
        self.assertNotIn("WantedBy=multi-user.target", text)

    def test_udev_rule_asks_systemd_on_power_supply_changes(self):
        text = RULE.read_text()
        self.assertIn('SUBSYSTEM=="power_supply"', text)
        self.assertIn('ACTION=="change"', text)
        self.assertIn("fawos-power-profile.service", text)

    def test_both_images_enable_the_unit(self):
        for recipe in ("recipe.yml", "recipe-desktop.yml"):
            self.assertIn("fawos-power-profile.service",
                          (ROOT / "recipes" / recipe).read_text())


if __name__ == "__main__":
    unittest.main()
