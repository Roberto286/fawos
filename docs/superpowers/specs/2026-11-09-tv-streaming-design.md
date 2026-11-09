# TV game streaming (Sunshine → Fire TV Stick 4K Max)

## Intent

Roberto bought a Fire TV Stick 4K Max to play PC games on the TV via Moonlight.
He wants the PC to be reachable from the couch without touching it: wake it,
land in Steam Big Picture, play. Daily use of the PC (~80% of physical power-ons)
stays the normal `roberto` desktop, protected by a password.

## Goals

- Sunshine host on the fawos image, tuned for the RX 6700 XT (RDNA2).
- A dedicated passwordless gaming user whose session is only Steam Big Picture + Sunshine.
- Wake-on-LAN from Moonlight on the TV powers the PC on and lands in the gaming session with no physical interaction.
- Physical power button still lands on the normal greeter; nothing logs in by itself.
- One shared Steam library used by both `roberto` and the gaming user.

## Non-goals

- AV1: the RX 6700 XT has no AV1 encoder. Use HEVC (H.264 fallback).
- Logging the gaming user in on the physical monitor for local play: local gaming stays in `roberto` (shared library).
- Wake on WLAN: the PC will be wired (`enp3s0`); Wi-Fi WoL from S5 does not work.
- Suspend/resume flows. Power-on is from S5 (off).

## Anti-goals (failure even if it "works")

- **Unwanted user switch.** Opening Moonlight on the TV while `roberto` has any session (active, locked, or background) must do nothing. The gaming user starts only when the seat shows the greeter and no user session exists.
- Any timeout-based autologin.
- Weakening `roberto`'s login (no autologin, no shared session with Sunshine).

## Constraints

- Immutable bootc image: everything goes through `recipes/recipe.yml` and `files/system/*` (see AGENTS.md).
- Login stack: greetd + dms-greeter (`files/system/etc/greetd/config.toml`, greeter user `greeter`).
- Steam today: user-scope flatpak `com.valvesoftware.Steam` in `roberto`, 49 GB in `~/.var/app/com.valvesoftware.Steam/.local/share/Steam/steamapps`.
- Board: ASUS PRIME B450-PLUS. WoL needs BIOS `Advanced > APM Configuration > Power On By PCI-E = Enabled` (user does this).
- Fedora's mesa ships without H.264/HEVC VA-API encode. Hardware HEVC encode needs `mesa-va-drivers-freeworld` (RPM Fusion) or an encoder path that does not use Fedora mesa VA-API.

## Approaches considered

1. **Gaming user always autologs in** — simplest, but costs a logout on ~80% of boots. Rejected.
2. **Greeter with timeout, then gaming autologin** — not deterministic. Rejected by Roberto.
3. **Moonlight-triggered login (chosen)** — a system listener on TCP 47989 runs only while the greeter is up. The first Moonlight request (it polls this port after sending WoL) starts the gaming session, if and only if no user session exists. Deterministic: driven by the TV actually calling.
4. **SMBIOS `Wake-up Type`** (`LAN Remote` vs `Power Switch`) to pick the user at boot — optional add-on only if a test on this board shows distinct values after the cable is in. Not part of this build.
5. **No second user, Sunshine in `roberto`** — needs `roberto` autologin; exposes data. Rejected.

Shared library options: shared folder (chosen), Steam only in gaming user, two separate libraries.

## Design (decided)

- **Gaming user**: dedicated local user (name: builder's call, e.g. `gaming`), password locked. It is only ever entered via the trigger, never typed at the greeter.
- **Session**: `gamescope` running Steam Big Picture (`steam -gamepadui` / `-steamos3`-style) as the session command; Sunshine runs as a user service inside that session only.
- **Trigger service** (system):
  - Listens on TCP 47989 while greetd shows the greeter.
  - On a connection: checks via logind that the only session on seat0 is the `greeter` class and there is no `user`-class session for any user. If not, drops the connection and does nothing.
  - If yes: starts the gaming session through greetd (greetd only supports `initial_session` at its own start, so: restart greetd once with a config that has `initial_session` for the gaming user; the persistent `/etc/greetd/config.toml` is not changed). Then releases the port so Sunshine can bind it.
  - When the gaming user logs out, greetd falls back to the normal greeter and the listener is armed again.
- **Sunshine**: system package on the image; uinput udev access and KMS capture capability as Sunshine requires; HEVC via VA-API; firewall ports opened if a firewall is active on the image.
- **Shared library**: `/var/games` (group-owned, setgid, writable by `roberto` and the gaming user). Steam flatpak gets filesystem access to it for both users. Moving the existing 49 GB from `roberto`'s library into `/var/games` is a one-time manual step (Steam "Move install folder"), documented for Roberto.
- **WoL**: NetworkManager default `ethernet.wake-on-lan=magic` so the future wired connection on `enp3s0` keeps WoL armed at shutdown.
- **Moonlight on the TV**: Roberto installs it on the Fire Stick and pairs once with Sunshine.
- **Stray trigger (accepted, Roberto's call)**: if Moonlight is open on the TV while the PC boots from the power button or after `roberto` logs out, its poll logs the gaming user in. Recovery: shut down or log out of the gaming session. No boot-time window, no source-IP filter. Anyone on the LAN can trigger the login; the stream itself stays protected by Sunshine pairing.
- **Monitor**: physical monitor is off while the gaming session runs (it is passwordless, so it must not sit visible). Mechanism is the builder's call (DPMS off, or headless/virtual output for gamescope).
- **End of streaming (Roberto's call)**: when the Moonlight stream ends, the PC powers off. The next boot re-arms the trigger, so no logout path is needed. Natural hook: Sunshine app `prep-cmd` undo command.
- **RPM Fusion (my call, not yet confirmed)**: add RPM Fusion and swap in `mesa-va-drivers-freeworld` for HEVC/H.264 hardware encode. Applies to the desktop image only.

## Image structure (Roberto's call)

Roberto runs fawos on two machines: this desktop (development + gaming) and a laptop (development + general purpose). Gaming-host pieces must not land on the laptop.

- Shared core in a common recipe; `recipes/recipe.yml` stays the laptop/general image.
- A second recipe for this desktop includes the core and adds: Sunshine, gamescope, RPM Fusion, the gaming user, the trigger, `/var/games`, WoL.
- Separate published image (e.g. `ghcr.io/roberto286/fawos-desktop`), added to the CI matrix; the desktop moves over with `bootc switch`.
- Module order constraints (`initramfs`, `signing` last) may need two includes around the desktop additions. Builder must verify BlueBuild's include syntax against the CI version.
- Open: whether the monthly ISO builds for one or both images; default is the current one only.

## Left to the builder

- Exact gaming user name and how it is created (sysusers vs. first-boot unit), keeping `/var/home` conventions (see AGENTS.md "Homes").
- Sunshine source (LizardByte COPR vs. other) given Fedora 45 availability. If no COPR exists for f45, report it rather than falling back silently.
- How the gaming user gets Steam (system-scope flatpak vs. user-scope), as long as both users use `/var/games`.
- Listener implementation (socket-activated unit + small script is the expected shape) and how it is disarmed while any session exists.
- gamescope output resolution vs. the 4K TV client.
- Tests for any new shell logic, following `tests/` conventions.
