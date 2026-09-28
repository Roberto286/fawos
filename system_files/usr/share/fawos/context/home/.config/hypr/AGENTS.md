# ~/.config/hypr — fawos

`hyprland.lua` here is **not** stock Hyprland config and **not**
chezmoi-managed — it's compiled by a custom Lua DSL (`hl.*`) shipped by the
same `lionheartp/Hyprland` COPR build that fawos installs Hyprland from, and
it's owned by the `fawos` OS image repo
(`system_files/etc/skel/.config/hypr/`), not by the dotfiles repo. Reason:
the DSL only works against fawos's exact Hyprland/DMS COPR builds — it has
zero portability value on any other system, so keeping it in the OS repo
(instead of dotfiles) keeps fixes that touch both the installed packages and
the config in one atomic commit.

- `hl.on("hyprland.start", ...)` autostarts `dms run --daemon` (the DMS
  shell) and `hypridle` (idle/lock daemon).
- `hypridle.conf`/`hyprlock.conf` sit alongside it, same ownership.
- To change anything here durably: edit the `fawos` repo's
  `system_files/etc/skel/.config/hypr/hyprland.lua` and rebuild — a live
  edit is local-only and lost on the next home sync/reinstall.
