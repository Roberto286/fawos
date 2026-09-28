# fawos — System Entry Point

You are on **fawos**, a custom bootc (Fedora Atomic) immutable Linux image. The
root filesystem is read-only at runtime except `/etc` and `/var` (OSTree/bootc
managed) — package installs via `dnf5` do NOT persist across reboots; the
image is rebuilt from source instead (`github.com/roberto286/fawos`).

## Layout
- `/etc/AGENTS.md` — what lives under `/etc` in fawos and why.
- `/usr/AGENTS.md` — shipped systemd units, bootc install config.
- `/var` — only `/var/lib/flatpak` is baked by fawos; everything else under
  `/var` is runtime state seeded by OSTree/systemd-tmpfiles, never source
  content (a `bootc container lint` constraint, not a style choice).
- `~/AGENTS.md` — per-user entry point (home directory conventions, dotfiles,
  dev tooling, project layout).

## Changing this system
Every file here is built from `github.com/roberto286/fawos`
(`build_files/` domain scripts + `system_files/` static overlay). To change
anything durable (a package, a config default, a systemd unit), edit that
repo and rebuild — editing files directly on a running fawos machine is lost
on the next `bootc upgrade`.
