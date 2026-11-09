# Desktop image: TV game streaming

`ghcr.io/roberto286/fawos-desktop` (recipe `recipes/recipe-desktop.yml`) adds Sunshine, gamescope, a passwordless `gaming` user and a Moonlight-triggered login on top of the common core. The laptop keeps `fawos`.

## How it behaves

- Power button: normal greeter, log in as `roberto`.
- Wake-on-LAN from Moonlight: PC boots to the greeter. Moonlight's poll on TCP 47989 makes `fawos-gaming-trigger` restart greetd with an `initial_session` for `gaming` (Steam Big Picture in gamescope, Sunshine running).
- The trigger does nothing if any non-greeter session exists (including a locked `roberto`).
- Stream ends: Sunshine's app undo command powers the PC off.
- Stray trigger (Moonlight open on the TV while you boot with the button): shut down or log out of `gaming`.

## One-time steps

1. BIOS: `Advanced > APM Configuration > Power On By PCI-E = Enabled`. Connect the cable (`enp3s0`).
2. `sudo bootc switch ghcr.io/roberto286/fawos-desktop`, reboot.
3. `sudo usermod -aG games roberto`, then log out and in.
4. Move the Steam library to `/var/games` (Steam: Settings > Storage > add drive, move install folder).
5. `flatpak override --user --filesystem=/var/games com.valvesoftware.Steam`
6. Pair Moonlight: reach the Sunshine web UI at `https://<pc-ip>:47990` from a `gaming` session and enter the PIN from Moonlight. The first run needs one manual trigger (`curl <pc-ip>:47989` at the greeter).
7. Optional WoL wake-type test: power off, wake by magic packet, `sudo dmidecode -s system-wake-up-type`; repeat with the button.

## Unverified on hardware

- DDC/CI monitor-off (`/usr/libexec/fawos/monitor-off`) needs a monitor with DDC/CI enabled; failure is ignored.
- Poweroff fires when the Sunshine app ends. Check "quit" versus "disconnect" in Moonlight.
- Firewall ports (47984-47990 TCP, 47998-48000 UDP) if a firewall is active.
