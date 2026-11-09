# TV Game Streaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `fawos-desktop` image that hosts Sunshine for a Fire TV Stick, with a passwordless gaming user started only by a Moonlight poll at the greeter, shared Steam library, PC powers off when the stream ends.

**Architecture:** Core modules move to `recipes/common.yml`; `recipe.yml` (laptop) and new `recipe-desktop.yml` include them. A socket-activated trigger on TCP 47989 checks logind, then restarts greetd with a generated `initial_session` for the gaming user.

**Tech Stack:** BlueBuild, greetd, systemd, logind (`loginctl`), Sunshine, gamescope, RPM Fusion, bash, Python `unittest`.

**Spec:** `docs/superpowers/specs/2026-11-09-tv-streaming-design.md`

## Global Constraints

- No AV1; HEVC with H.264 fallback (RX 6700 XT).
- Trigger fires only if seat0 has the `greeter` session and no `user`-class session exists (active, locked or background). No timeouts.
- `roberto` login unchanged: no autologin, password kept.
- Stream end means poweroff. Physical monitor off during the gaming session.
- Shared library at `/var/games`, setgid, group-writable by `roberto` and the gaming user.
- Gaming user password locked, home under `/var/home` (AGENTS.md "Homes").
- Do not add a fallback kernel. Do not touch `.omp/`. Do not commit `todo.md`.
- Commits: conventional, lowercase scope. Check `git status -sb` and branch `main` first.
- Missing Sunshine COPR for Fedora 45: stop and report, no silent fallback.
- Gaming-only content lives in the desktop recipe; laptop image must not get it.

## Review Focus

- Moonlight poll while `roberto` is locked: trigger must do nothing (test in Task 3).
- Poll while no session and greeter not yet up (early boot): must not trigger (Task 3).
- Two polls in quick succession: greetd restarts once only (Task 3).
- Poll arrives while gaming session already runs: listener is not bound, Sunshine answers (Task 4 manual check).
- Stream disconnects but app stays open ("disconnect" vs "quit"): PC may not power off (Task 4 manual check).

---

### Task 1: Split recipes and CI

**Files:**
- Create: `recipes/common.yml`, `recipes/recipe-desktop.yml`
- Modify: `recipes/recipe.yml`, `.github/workflows/build.yml` (matrix + validate list)
- Test: `tests/test_recipes.py`

**Interfaces:**
- Produces: `common.yml` holds everything now in `recipe.yml` modules up to and including the CachyOS kernel `script` module (lines 10-121). `recipe-desktop.yml` has `name: fawos-desktop` and slots for desktop modules before `initramfs`.

- [ ] **Step 1:** Check the BlueBuild `from-file` module syntax in the docs for the version used by `blue-build/github-action` v1.13 (`https://blue-build.org/reference/module/`). Note the exact form.
- [ ] **Step 2: Write `tests/test_recipes.py`** (needs PyYAML; skip if missing): `test_recipes_parse`, `test_desktop_has_gaming_pieces_laptop_does_not` (string `sunshine` in `recipe-desktop.yml` and absent from `recipe.yml` and `common.yml`), `test_initramfs_and_signing_are_last` (in each of the two recipes, the last modules in order are `initramfs`, ..., `signing`, `systemd`).
- [ ] **Step 3:** Run `python3 -m unittest tests.test_recipes -v`. Expected: FAIL.
- [ ] **Step 4:** Create `common.yml` (modules 10-121 of today's file; no `name`/`base-image` header unless `from-file` needs it). Reduce `recipe.yml` to header + `from-file: common.yml` + the remaining modules (`initramfs`, flatpaks, `signing`, `systemd`). Create `recipe-desktop.yml` with `name: fawos-desktop`, same header, `from-file: common.yml`, then the same trailing modules, with an empty slot comment before `initramfs`.
- [ ] **Step 5:** Add `recipe-desktop.yml` to the build matrix and to the `validate` file list in `build.yml`.
- [ ] **Step 6:** Run tests. Expected: PASS for parse and order tests.
- [ ] **Step 7: Commit** `refactor(recipes): split common core from per-machine recipes`.

### Task 2: Desktop packages, repos and user

**Files:**
- Modify: `recipes/recipe-desktop.yml`
- Create: `files/system-desktop/usr/lib/sysusers.d/gaming.conf`, `files/system-desktop/usr/lib/tmpfiles.d/fawos-games.conf`, `files/system-desktop/usr/lib/udev/rules.d/60-sunshine.rules`, `files/system-desktop/etc/NetworkManager/conf.d/50-fawos-wol.conf`
- Modify: `recipes/recipe-desktop.yml` to add a `files` module with `source: system-desktop`

**Interfaces:**
- Produces: user `gaming` (uid system-allocated, locked password, home `/var/home/gaming`, groups `video`, `input`, `render`, `games`); group `games` containing `roberto` and `gaming`; `/var/games` mode `2775 root:games`.

- [ ] **Step 1:** Add to `recipe-desktop.yml` before `initramfs`: a `files` module for `system-desktop`; a `dnf` module with RPM Fusion repos (`rpmfusion-free` and `rpmfusion-nonfree` release RPMs), the Sunshine COPR for Fedora 45 (verify it exists; if not, stop and report), packages `sunshine`, `gamescope`, and a swap `mesa-va-drivers` to `mesa-va-drivers-freeworld`. Verify package names against Fedora 45 repos.
- [ ] **Step 2:** `gaming.conf` (sysusers): create user `gaming` with home `/var/home/gaming` and shell `/bin/bash`, and group `games`. `roberto` membership in `games` is added by a first-boot unit or `usermod` hint documented in Task 5, since `roberto` is not an image user.
- [ ] **Step 3:** `fawos-games.conf` (tmpfiles): `d /var/games 2775 root games -`. udev rule: `KERNEL=="uinput", GROUP="input", MODE="0660", OPTIONS+="static_node=uinput"`. NetworkManager conf: `[connection]` with `ethernet.wake-on-lan=magic`.
- [ ] **Step 4:** Add a `script` module: `setcap cap_sys_admin+p $(readlink -f /usr/bin/sunshine)`, and `passwd -l gaming` equivalent via sysusers locked entry (`u gaming - ...` leaves it locked).
- [ ] **Step 5:** Extend `tests/test_recipes.py` with `test_system_desktop_files_not_in_laptop_recipe`. Run all tests, expect PASS.
- [ ] **Step 6: Commit** `feat(desktop): add sunshine, gamescope, gaming user and shared games dir`.

### Task 3: Trigger (TDD)

**Files:**
- Create: `files/system-desktop/usr/libexec/fawos/gaming-trigger`, `files/system-desktop/etc/systemd/system/fawos-gaming-trigger.socket`, `fawos-gaming-trigger.service`
- Test: `tests/test_gaming_trigger.py`

**Interfaces:**
- Produces: `gaming-trigger` bash script. Env overrides for tests: `FAWOS_LOGINCTL` (path to a fake `loginctl`), `FAWOS_GREETD_CONFIG` (output path, default `/run/greetd/gaming.toml`), `FAWOS_SYSTEMCTL` (fake). Exit 0 always. Behaviour: reads `loginctl list-sessions --no-legend -o json` equivalent via `show-session`; if any session of `Class=user` exists, or none of `Class=greeter` exists, do nothing; otherwise write a greetd config equal to `/etc/greetd/config.toml` plus `[initial_session]` with `command = "gamescope-session"` and `user = "gaming"`, then `systemctl restart greetd`. A lock (`flock` on `/run/fawos-gaming-trigger.lock`) prevents a second restart.

- [ ] **Step 1: Write tests** using fake `loginctl`/`systemctl` shell stubs in a temp dir: `test_user_session_blocks_trigger` (including a locked one), `test_no_greeter_session_blocks_trigger`, `test_greeter_only_writes_config_and_restarts_once`, `test_second_call_within_lock_does_not_restart`, `test_generated_config_has_initial_session_for_gaming`.
- [ ] **Step 2:** Run, expect FAIL.
- [ ] **Step 3:** Implement the script with `set -uo pipefail`.
- [ ] **Step 4:** Socket unit `ListenStream=47989`, `Accept=no`; service `Type=oneshot` runs the script (it closes the connection by exiting). Greetd must start with the generated config only on trigger: add a drop-in `greetd.service.d/gaming.conf` with `ExecStart=` using `/usr/bin/greetd --config` pointing to the generated file if it exists, otherwise `/etc/greetd/config.toml` (small wrapper script `greetd-config`). The wrapper deletes the generated file after greetd starts so the next boot is a normal greeter.
- [ ] **Step 5:** Order the socket `Before=` nothing; add `Conflicts=` is not needed because Sunshine binds only in the gaming session and the socket is stopped by `fawos-gaming-trigger-stop` run by the session start (Task 4).
- [ ] **Step 6:** Run tests, expect PASS. Enable the socket in the `systemd` module of `recipe-desktop.yml`.
- [ ] **Step 7: Commit** `feat(desktop): add moonlight-triggered gaming login`.

### Task 4: Gaming session, Sunshine, monitor, poweroff

**Files:**
- Create: `files/system-desktop/usr/bin/gamescope-session`, `files/system-desktop/usr/lib/systemd/user/sunshine.service` override if package lacks one, `files/system-desktop/usr/libexec/fawos/stream-undo`
- Test: `tests/test_stream_undo.py`

**Interfaces:**
- Consumes: Task 3 socket `fawos-gaming-trigger.socket`.
- Produces: `gamescope-session` (stops the trigger socket via `systemctl stop fawos-gaming-trigger.socket` through a polkit rule or sudoers entry for `gaming`; starts Sunshine user service; execs `gamescope -- steam -gamepadui`). `stream-undo` (powers off with `systemctl poweroff` through polkit for `gaming`).

- [ ] **Step 1:** Write `tests/test_stream_undo.py`: `test_undo_calls_poweroff` with a fake `systemctl` via `FAWOS_SYSTEMCTL`.
- [ ] **Step 2:** Implement `stream-undo` and run the test.
- [ ] **Step 3:** Write `gamescope-session`: monitor off via `wlr-randr --output <name> --off` or headless output (builder's call; verify what works under gamescope on the RX 6700 XT).
- [ ] **Step 4:** Ship Sunshine `apps.json` default with one app "Steam Big Picture", `cmd` = `steam -gamepadui`, `prep-cmd` undo = `/usr/libexec/fawos/stream-undo`. Add polkit rules for `gaming`: `org.freedesktop.systemd1.manage-units` limited to the trigger socket, and `org.freedesktop.login1.power-off`.
- [ ] **Step 5:** Register a wayland session `.desktop` for the gaming user if greetd needs one; otherwise the `command` in Task 3 is enough.
- [ ] **Step 6:** Run all tests; expect PASS.
- [ ] **Step 7: Commit** `feat(desktop): add gamescope session, sunshine app and poweroff on stream end`.

### Task 5: Docs and migration notes

**Files:**
- Modify: `AGENTS.md` (layout: `files/system-desktop`, two recipes, new gotchas), `README.md` if it describes the image.
- Create: `docs/desktop-streaming.md`

- [ ] **Step 1:** Update `AGENTS.md`: two recipes; `from-file`; desktop-only files dir; trigger behaviour; poweroff on stream end.
- [ ] **Step 2:** Write `docs/desktop-streaming.md` with the one-time steps for Roberto: BIOS `Power On By PCI-E`, cable, `sudo usermod -aG games roberto`, move the Steam library to `/var/games` (Steam "Move install folder"), grant flatpak access (`flatpak override --user --filesystem=/var/games com.valvesoftware.Steam`), `sudo bootc switch ghcr.io/roberto286/fawos-desktop`, pair Moonlight, test WoL and `sudo dmidecode -s system-wake-up-type`.
- [ ] **Step 3:** Run `python3 -m unittest discover -s tests`; expect PASS.
- [ ] **Step 4: Commit** `docs(desktop): document streaming setup`.

## Manual verification (after CI publishes `fawos-desktop`)

1. Boot to greeter, run `curl -s --max-time 5 http://127.0.0.1:47989/` from another host: gaming session starts, monitor goes off.
2. Log in as `roberto`, lock, repeat the curl: nothing happens.
3. Stream from Moonlight, quit the app: PC powers off. Also test "disconnect" without quit.
