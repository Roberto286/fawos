# ~/.config — fawos

Dotfiles here are managed by **chezmoi**, applied idempotently on every login
by `chezmoi-bootstrap.service` from `github.com/Roberto286/dotfiles`
(chezmoi source-state repo, `dot_*` naming convention). To change a managed
dotfile, edit it through `chezmoi edit <path>` or edit the source repo
directly — a raw edit under `~/.config/...` gets overwritten on the next
`chezmoi apply` if that file is chezmoi-managed.

**Not chezmoi-managed** (owned by the `fawos` OS image repo instead, copied
at build time — see `~/.config/hypr/AGENTS.md`): `hypr/`.

Chezmoi-managed: `fish/`, `nvim/`, `zed/`, `opencode/`, plus `~/.gitconfig`
and friends at `$HOME` root (git's own convention, not under `.config`).
