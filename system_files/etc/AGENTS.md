# /etc — fawos

Managed by OSTree: files here merge across `bootc upgrade` (unlike the
read-only rest of `/`), so this is where fawos ships default configs a user
may locally override.

- `greetd/config.toml` — login/display manager, launches `dms-greeter`
  running Hyprland as the `greeter` user.
- `mise/config.toml` — global pinned dev-tool versions (node/python/go/...),
  read by every user's `mise activate`; actual toolchains install per-user
  into `~/.local/share/mise` at first login (see `mise-bootstrap.service`).
- `skel/` — no longer the primary way fawos seeds a user's home (see
  `~/AGENTS.md` for why); still used for genuinely one-shot static dotfiles
  not covered by chezmoi or the `fawos-context-sync` mechanism.
- `fish/conf.d/`, `profile.d/` — shell activation snippets (mise, podman
  `DOCKER_HOST`, the welcome banner).
- `sysusers.d/99-roberto.conf` — declarative account/group provisioning for
  the `roberto` user (`systemd-sysusers` format).

Source of truth for all of this: `system_files/etc/` in the `fawos` repo.
