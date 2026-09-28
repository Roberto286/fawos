# ~/.local/share — fawos

- `mise/` — actual installed dev-tool versions (node/python/go/...), pulled
  per-user at first login by `mise-bootstrap.service` from the global pins
  in `/etc/mise/config.toml`. Genuinely per-user, never baked into the
  image (would bloat every pull for a benefit that only exists at first
  boot).
- `chezmoi/` — chezmoi's own state (source checkout, cache). Managed by
  `chezmoi apply`, not meant for manual edits.
