# fawos

BlueBuild recipe repo that builds the immutable `ghcr.io/roberto286/fawos` bootc image and a monthly ISO. There is no app code; changes are to YAML, shell, and dotfile-on-image content.

## Layout

- Two images, three recipes: `recipes/common.yml` (shared modules: base config, packages, kernel) is pulled in with `from-file` by `recipes/recipe.yml` (`fawos`, laptop/general) and `recipes/recipe-desktop.yml` (`fawos-desktop`, gaming host). Both keep `initramfs`, flatpaks, `signing`, `systemd` last. Modules run top-to-bottom. Schema: `# yaml-language-server: $schema=...` at the top. Gaming-only things go in the desktop recipe, never in `common.yml`.
- `files/system/*` is copied verbatim to the image root `/` by the `files` module — e.g. `files/system/usr/bin/fawos-update` becomes `/usr/bin/fawos-update`. `files/system-desktop/*` is the same for the desktop image only. Nothing else touches those paths.
- Desktop streaming (Sunshine, `gaming` user, Moonlight-triggered login, poweroff at stream end): see `docs/desktop-streaming.md`. `tests/test_recipes.py` needs PyYAML and skips without it.
- `modules/` is empty (only `.gitkeep`); `Containerfile` and `.bluebuild-scripts_*` are build artifacts (gitignored).

## Verification (local)

- Tests: `python3 -m unittest discover -s tests` from the repo root (stdlib only, fast). The root-rejection test auto-skips when not root.
- Full image builds run in CI only (`.github/workflows/build.yml`), not locally.
- Markdown-only commits skip the image build (CI `paths-ignore: **.md`); any other path change publishes a new image.

## Editing `fawos-update`

`files/system/usr/bin/fawos-update` has a strict contract the tests pin down:

- Accepts only `--check` and step names (`image flatpak dotfiles dms mise`); anything else → exit 2. Running as root (even via sudo) → exit 2.
- Image, flatpak and mise updates are held back 7 days (`MIN_AGE_DAYS`): image = newest daily `YYYYMMDD` tag ≥7 days old via `bootc switch`, flatpak = newest commit ≥7 days old via `--commit`, mise = `--minimum-release-age`. Never downgrades. `--check` only reports.
- Failed update steps are accumulated and reported, then exit 1 — steps that don't depend on each other must keep running after one fails.
- Shell is bash with `set -uo pipefail` and INT/TERM traps (exit 130/143).
- Change any of these and `tests/test_fawos_update.py` breaks.

## Image/known gotchas

- Stock Fedora `kernel` is *removed* and `kernel-cachyos` (COPR) replaces it. Missing COPR = build failure, on purpose — do not add a fallback kernel. Dracut runs with `DRACUT_NO_XATTR=1` in both the kernel and initramfs modules; needed for builds to pass.
- The chezmoi module bakes in `Roberto286/dotfiles` with `file-conflict-policy: skip` (local edits are kept; `fawos-update` lists drift); user-facing changes to those configs belong in that dotfiles repo, not here.
- Filesystem: neither Anaconda nor `bootc install` has a fs picker. The ISO's Anaconda profile (`fedora` in `install.img`, matched on `ID=fedora`) provisions BTRFS with `zstd:1`; `files/system/usr/lib/bootc/install/50-fawos.toml` makes `bootc install to-disk` default to BTRFS too. Don't add an fs choice to the ISO — the jasonn3 builder cannot express it.
- Homes: `/home` is a symlink to `/var/home` and `/etc/default/useradd` has `HOME=/var/home`, so runtime `useradd` is correct. Anaconda's user spoke pre-fills the home field from the *empty* target sysroot (falls back to `/home`), so an account created during install can be recorded as `/home/<user>`. `fawos-normalize-home.service` rewrites those `/etc/passwd` entries to `/var/home` at boot — keep it enabled, it is the only install-path-agnostic fix.
- Power profiles: `fawos-power-profile.service` (both images) runs `files/system/usr/libexec/fawos/power-profile` — no battery → `performance`, on AC → `performance`, on battery ≥50% → `balanced`, below that → `power-saver`; `files/system/usr/lib/udev/rules.d/70-fawos-power-profile.rules` re-runs it on every `power_supply` change. It is pulled in by `graphical.target` on purpose: Fedora's `power-profiles-daemon.service` is `After=multi-user.target`, so a unit pulled in by `multi-user.target` and ordered after the daemon forms an ordering cycle and systemd silently deletes its job (that is why the old `fawos-desktop-performance.service` never ran). DankMaterialShell's own "Switch to power profile" setting (`acProfileName`/`batteryProfileName` in the dotfiles repo) covers the plug/unplug switch; the service adds the <50% tier and the desktop case. If `powerprofilesctl set` fails (amd-pstate + Ryzen 5000: a per-policy `boost` write returns EINVAL and the daemon aborts the whole profile) the script writes cpufreq directly, so the CPU is right but DMS shows a stale profile until PPD is fixed.
- Firewall: `files/system/etc/firewalld/zones/public.xml` is a full replacement of the stock zone (there are no drop-ins for zones), so it re-declares `ssh`, `mdns` and `dhcpv6-client` before adding LocalSend's `53317/tcp`+`53317/udp`. Editing it with `firewall-cmd --permanent` on a running machine regenerates the file from the *runtime* zone — re-add the ports or the next commit silently closes them. Outgoing traffic is never filtered, so a missing inbound port shows up as "sending works one way only".
- Snapshots: `snapper` config `home` targets `/var/home` (not `/`, which would pin the ostree repo inside the root subvolume). `fawos-snapper-home.service` creates `.snapshots` on first boot and no-ops when `/var/home` is not a subvolume. No boot-menu snapshots: grub-btrfs is not packaged in Fedora and does not work with ostree/BLS entries; OS rollback is `bootc rollback`.

## Conventions

- Commit messages: conventional commits with lowercase scope, e.g. `feat(packages): ...`, `fix(gh-actions): ...`.
- `.omp/` holds the private cosign signing keys; it is gitignored — never add or commit anything from it.
- `todo.md` is the user's personal task list (in Italian); leave it out of unrelated commits.
- Always check `git status -sb` first and confirm you're on `main` before committing: the working tree has been found sitting on a `dependabot/*` branch with commits landing into it unnoticed.
