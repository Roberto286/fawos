# fawos

BlueBuild recipe repo that builds the immutable `ghcr.io/roberto286/fawos` bootc image and a daily ISO. There is no app code; changes are to YAML, shell, and dotfile-on-image content.

## Layout

- `recipes/recipe.yml` is the single source of truth for the image: base image, COPRs, packages, kernel replacement, flatpaks, systemd presets. Modules run top-to-bottom in listed order. Schema: `# yaml-language-server: $schema=...` at the top.
- `files/system/*` is copied verbatim to the image root `/` by the `files` module — e.g. `files/system/usr/bin/fawos-update` becomes `/usr/bin/fawos-update`. Nothing else touches those paths.
- `modules/` is empty (only `.gitkeep`); `Containerfile` and `.bluebuild-scripts_*` are build artifacts (gitignored).

## Verification (local)

- Tests: `python3 -m unittest discover -s tests` from the repo root (stdlib only, fast). The root-rejection test auto-skips when not root.
- Full image builds run in CI only (`.github/workflows/build.yml`), not locally.
- Markdown-only commits skip the image build (CI `paths-ignore: **.md`); any other path change publishes a new image.

## Editing `fawos-update`

`files/system/usr/bin/fawos-update` has a strict contract the tests pin down:

- No arguments allowed → exit 2; running as root (even via sudo) → exit 2.
- Failed update steps are accumulated and reported, then exit 1 — steps that don't depend on each other must keep running after one fails.
- Shell is bash with `set -uo pipefail` and INT/TERM traps (exit 130/143).
- Change any of these and `tests/test_fawos_update.py` breaks.

## Image/known gotchas

- Stock Fedora `kernel` is *removed* and `kernel-cachyos` (COPR) replaces it. Missing COPR = build failure, on purpose — do not add a fallback kernel. Dracut runs with `DRACUT_NO_XATTR=1` in both the kernel and initramfs modules; needed for builds to pass.
- The chezmoi module bakes in `Roberto286/dotfiles` with `file-conflict-policy: replace`; user-facing changes to those configs belong in that dotfiles repo, not here.

## Conventions

- Commit messages: conventional commits with lowercase scope, e.g. `feat(packages): ...`, `fix(gh-actions): ...`.
- `.omp/` holds the private cosign signing keys; it is gitignored — never add or commit anything from it.
- `todo.md` is the user's personal task list (in Italian); leave it out of unrelated commits.
