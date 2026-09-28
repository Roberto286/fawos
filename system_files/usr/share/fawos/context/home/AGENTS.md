# ~/AGENTS.md — fawos home entry point

This is a **fawos** machine (custom bootc/Fedora Atomic image — see
`/AGENTS.md` for the system-level picture). This file and everything it
points to is synced by `fawos-context-sync.service` on every login from
`/usr/share/fawos/context/home/` — editing it directly in your home gets
overwritten on next login; change it in the `fawos` repo instead.

## Index
- `~/.config/AGENTS.md` — dotfile management (chezmoi).
- `~/.config/hypr/AGENTS.md` — Hyprland config, the custom `hl.*` DSL, and DMS.
- `~/.local/share/AGENTS.md` — mise toolchains, chezmoi state.
- `~/code/AGENTS.md` — where projects live and how they're organized.

## Quick facts
- Shell: `fish`. Terminal: `ghostty`. File manager: `dolphin`. App
  launcher/picker: `hyprlauncher` (`Super+R`).
- AI agent of choice: `fawos-agent` (picks among `omp`/`claude`/`opencode`/
  `codex`/`pi`, `Super+Shift+Ctrl+A` or run `fawos-agent --choose` to change).
- System update: `fawos-update` (bootc + flatpak + mise, one command).
- Containers: podman only (no Docker Engine); `DOCKER_HOST` is wired to the
  rootless podman socket for Docker-API tools like lazydocker.
