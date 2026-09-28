# /usr — fawos

Read-only at runtime (part of the OSTree-managed image tree, only replaced
whole on `bootc upgrade`).

- `lib/systemd/system/` — system-level units shipped by fawos (e.g.
  `fawos-power-default.service`).
- `lib/systemd/user/` — per-user units, enabled via symlinks into
  `default.target.wants/` at build time (`mise-bootstrap.service`,
  `chezmoi-bootstrap.service`, `fawos-context-sync.service`, ...).
- `lib/bootc/install/` — bootc installer defaults (root filesystem type:
  ext4).
- `share/fawos/context/home/` — canonical source for the per-user
  `AGENTS.md` tree, synced into `$HOME` by `fawos-context-sync.service` on
  every login (see `~/AGENTS.md` for why this isn't just `/etc/skel`).
- `bin/fawos-update`, `bin/fawos-agent`, `bin/fawos-context-sync` — fawos's
  own scripts, all shipped here (FHS-standard location for system-local
  binaries; `/usr/local` on this image is a symlink to `/var/usrlocal` that
  doesn't exist at build time, so it's never used as a target).

Source of truth: `system_files/usr/` in the `fawos` repo.
