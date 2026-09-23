# Repository Guidelines

## Project Overview

`fawos` is a custom **bootc** (bootable OCI container) Linux image, forked from
[`ublue-os/image-template`](https://github.com/ublue-os/image-template). It is not
an application codebase — there is no compiled program. The "product" is a
container image (`Containerfile`) that layers Homebrew, a CachyOS kernel, and a
Hyprland/greetd/DMS desktop environment on top of `ghcr.io/ublue-os/base-main:latest`
(Fedora Atomic). CI publishes the image to GHCR (cosign-signed) and can turn it
into installable disk images (ISO/qcow2/raw) via `bootc-image-builder`.

## Architecture & Data Flow

```
Containerfile (multi-stage podman build)
 ├─ stage "brew"  : ghcr.io/ublue-os/brew:latest        (homebrew payload)
 ├─ stage "ctx"   : scratch + COPY build_files/ system_files/  (build-time context only)
 └─ final stage   : ghcr.io/ublue-os/base-main:latest
      ├─ COPY --from=brew /system_files /        (installs brew into image)
      ├─ RUN --mount=type=bind,from=ctx,...       (bind-mounts ctx as /ctx)
      │     └─ /ctx/build.sh                      (entry point, see below)
      └─ RUN bootc container lint                  (final validation, must pass)
```

`build.sh` (`build_files/build.sh`) is the orchestrator invoked from the
Containerfile:
1. `cp -avf "/ctx/system_files"/. /` — copies all of `system_files/` onto the
   image root (configs, users, skel dotfiles win over package defaults).
2. `source lib/common.sh` — loads shared helpers (`install_packages`,
   `enable_copr`/`disable_copr`, `enable_persistent_repo`).
3. Sources every `domains/*.sh` script in fixed order: `users kernel desktop
   terminal devtools containers apps gpu gaming power`. `users` always runs
   first (account/credential provisioning is foundational); `build.sh` itself
   contains no install logic of its own — it is a pure orchestrator.

Package manager is **`dnf5`** throughout (not `rpm-ostree`, not `apt`). Third-party
software comes from COPR repos, enabled just-in-time and disabled again after
install to avoid leaving stray metadata in the final layer:
- `bieszczaders/kernel-cachyos` — CachyOS kernel/kernel-core/kernel-modules (enabled → swapped → disabled), in `domains/kernel.sh`
- `avengemedia/danklinux` — `dms`, `dms-greeter` (left enabled), in `domains/desktop.sh`
- `lionheartp/Hyprland` — `Hyprland` (enabled → installed → disabled), in `domains/desktop.sh`
- `atim/lazygit`, `atim/lazydocker` (enabled → installed → disabled), in `domains/devtools.sh`

RPM Fusion (free + nonfree) is the one **persistent** repo — enabled via
`enable_persistent_repo` in `domains/gaming.sh` and never disabled (Steam and
friends need it available for the life of the image, unlike ephemeral COPRs).

Display chain at boot: **greetd** (`system_files/etc/greetd/config.toml`) → runs
`dms-greeter` as the `greeter` user → launches **Hyprland**, which autostarts
`dms run --daemon` per `system_files/etc/skel/.config/hypr/hyprland.lua`.

Local dev/CI orchestration is entirely `Justfile`-driven: `podman build` →
optional rechunk → tag → (CI only) push to GHCR + `cosign sign`. Disk images are
built separately from the pushed OCI image via `bootc-image-builder` (BIB),
configured per output type by `disk_config/*.toml`.

## Key Directories

| Path | Purpose |
|---|---|
| `Containerfile` | Image build entrypoint (multi-stage podman build) |
| `build_files/` | Shell scripts run **inside** the build — `build.sh` (pure orchestrator) + `lib/` + `domains/` + `packages/` |
| `build_files/lib/common.sh` | Shared helpers sourced by every domain script (`install_packages`, `enable_copr`/`disable_copr`, `enable_persistent_repo`) |
| `build_files/domains/` | One script per functional domain (`users`, `kernel`, `desktop`, `terminal`, `devtools`, `containers`, `apps`, `gpu`, `gaming`, `power`) — sourced in this fixed order by `build.sh` |
| `build_files/packages/*.txt` | Declarative package lists (one package per line, `#` comments) consumed by `install_packages` — one file per domain that needs one |
| `system_files/etc/mise/config.toml` | Global `mise` tool version pins (node/python/go/bitwarden-cli) |
| `system_files/etc/fish/conf.d/`, `system_files/etc/profile.d/` | Shell activation snippets (mise, podman `DOCKER_HOST`) |
| `system_files/usr/lib/systemd/user/` | Per-user systemd units (`podman.socket` enablement, `mise-bootstrap.service`) |
| `system_files/usr/bin/fawos-update` | Single-command updater shipped in the image (`bootc upgrade` + `flatpak update` + `mise upgrade`) — a system binary, not a `just` recipe |
| `system_files/` | Raw files copied verbatim onto the image root (`etc/`, `usr/lib/`) — treat as "the filesystem overlay" |
| `system_files/etc/greetd/` | greetd (display manager) config |
| `system_files/etc/skel/` | Dotfiles seeded into every new user's home (Hyprland config) |
| `system_files/usr/lib/sysusers.d/` | Declarative user/group provisioning (`systemd-sysusers`) |
| `system_files/usr/lib/bootc/install/` | bootc installer filesystem defaults (e.g. ext4 root) |
| `disk_config/` | BIB TOML configs: `disk.toml` (qcow2/raw), `iso.toml` (fawos ISO), `iso-gnome.toml`/`iso-kde.toml` (upstream template ISOs) |
| `.github/workflows/` | `build.yml` (image build+sign+push), `build-disk.yml` (disk image matrix build) |
| `Justfile` | All build/run/lint recipes — the primary interface to this repo |
| `image-template.env` | Env vars consumed by `Justfile` (`set dotenv-load`) — `IMAGE_NAME`, `REPO_ORGANIZATION`, `DEFAULT_TAG`, `BIB_IMAGE`, etc. |
| `disk_config/`, `cosign.pub`, `artifacthub-repo.yml` | Publishing/signing/metadata config |

There is no `src/` or `tests/` directory — this is infra/config, not application
code; "correctness" is validated by building the image and running `bootc
container lint` / `just lint`.

## Development Commands

Run everything through **`just`** (see `Justfile`); recipes load `image-template.env`
automatically via `set dotenv-load`.

```bash
just build                       # podman build (OCI + ArtifactHub labels, git SHA tag if clean tree)
just build myimage v1.0          # override $target_image / $tag
just build myimage v1.0 /path/to/secret   # 3rd optional arg: --secret file for roberto_password (CI-only in practice)
just ostree-rechunk               # rpm-ostree compose build-chunked-oci (classic rechunk, used in CI)
just rechunk                     # chunkah-based rechunk (newer, experimental — image pinned to :latest, TODO to pin digest)
just build-qcow2 / build-raw / build-iso   # container image -> bootable disk image via BIB
just rebuild-qcow2 / rebuild-raw / rebuild-iso  # rebuild container THEN disk image
just run-vm-qcow2 / run-vm-raw / run-vm-iso     # QEMU container, auto-opens http://localhost:<port>
just spawn-vm rebuild=1 type=qcow2 ram=6G       # systemd-vmspawn alternative to QEMU
just dev-switch                  # builds locally + `sudo bootc switch --transport containers-storage` (fast local iteration)
just lint                        # shellcheck every *.sh
just format                      # shfmt --write every *.sh
just check / just fix            # `just --unstable --fmt` on the Justfile/*.just files
just clean                       # removes build output/tempdirs
```

Requires: `just`, `podman`, `jq`. Linting additionally needs `shellcheck`/`shfmt`.
VM recipes need `qemu`/KVM (`/dev/kvm`) or `systemd-vmspawn`. Disk-image recipes
(`_build-bib`) run podman **rootful/privileged** — expect `sudo` prompts; the
`sudoif`/`_rootful_load_image` helpers transparently bridge rootless→rootful
podman storage.

There is no test suite. "Verification" = `just build` succeeds and `bootc
container lint` (run inside the Containerfile) passes, or a VM boots via
`just run-vm-qcow2`.

`fawos-update` is **not** a `just` recipe — it's a script baked into the built
image at `/usr/bin/fawos-update`, run on the deployed system (not from this
repo checkout) to update the bootc image, Flatpak apps, and mise-managed
language toolchains in one command.

## Code Conventions & Common Patterns

**Bash strict mode** is the norm, with three tiers seen across the codebase:
- `set -euo pipefail` — default for most Justfile recipes.
- `set -euox pipefail` / `set -ouex pipefail` — add `x` (xtrace) for build-critical recipes (`build`, `_build-bib`, `lint`, `format`, `dev-switch`, and `build_files/build.sh`).
- `set -xeuo pipefail` — xtrace-first variant (`rechunk`, `ostree-rechunk`, `_run-vm`, `spawn-vm`).

`build_files/lib/common.sh` and every `build_files/domains/*.sh` are **sourced**,
not executed — no shebang, no strict mode of their own (they inherit
`build.sh`'s `set -ouex pipefail`). Domain scripts call the shared helpers from
`lib/common.sh` (`install_packages`, `enable_copr`/`disable_copr`,
`enable_persistent_repo`) instead of hand-rolling
`dnf5`/COPR logic — follow this pattern for any new domain: declare packages in
`packages/<domain>.txt` where a flat list suffices, keep repo-enable/disable
logic (which varies per domain) directly in the domain script.

**Naming**: Justfile public recipes are `kebab-case` (`build-qcow2`,
`dev-switch`); private/internal recipes are prefixed `_` (`_build-bib`,
`_rootful_load_image`, `_run-vm`) and hidden from `just --list`.

**Argument handling**: recipes take `$param=default` positional args (e.g.
`build-qcow2 $target_image=("localhost/" + image_name) $tag=default_tag`),
letting every recipe run parameterless with sane defaults, or be called
explicitly (`just build myimage v1.0`). Multi-flag command lines are built as
bash arrays (`LABELS=(...)`, `BUILD_ARGS=(...)`) and expanded with
`"${array[@]}"` — follow this instead of long inline strings.

**Cleanup discipline**: any recipe creating temp state uses `mktemp -d`
immediately followed by `trap 'rm -rf "$DIR"' EXIT` (see `rechunk`,
`_build-bib`). Match this when adding new recipes that touch the filesystem.

**Privilege escalation**: never call `sudo` directly in a new recipe — route
through the `sudoif` helper (checks `UID`, `SUDO_USER`, `SSH_ASKPASS`/`DISPLAY`
for `sudo --askpass` vs plain `sudo`) and `_rootful_load_image` (moves a
rootless-podman image into rootful storage via `podman image scp`, falling back
to `sudo podman pull`).

**Comments**: mixed English/Italian throughout (`kernel.sh` comments are in
Italian; `dev-switch` prints an Italian reboot message). Match the existing
script's language rather than forcing consistency across files.

**Idempotency in `dms.sh`**: guards directory/file operations with
`if [ -d ... ]` / existence checks before `chmod`/`mkdir` — replicate this for
any config-writing addition to `build_files/`, since the build may re-run
against a warm cache.

## Important Files

- `Containerfile` — the actual build definition; change the `FROM` line to
  rebase onto a different Universal Blue/Fedora Atomic image.
- `build_files/build.sh` — pure orchestrator, no install logic of its own;
  add new package installs / COPRs inside the relevant `build_files/domains/*.sh`
  (or add a new domain script and append it to the `for domain in ...` list).
- `build_files/domains/users.sh` — security-critical: provisions the `roberto`
  account and sets its password **only** from a CI-supplied secret
  (`ROBERTO_PASSWORD` GitHub Actions secret, never a committed file); local
  builds skip the password step by design (see `--secret ...,required=false`
  in `Containerfile`).
- `system_files/usr/bin/fawos-update` — single-command updater for a deployed
  machine; keep it in sync if new update-able subsystems are added (e.g. a
  future package manager for CLI tools).
- `system_files/` — anything placed here is copied verbatim onto the image
  root at build time (`cp -avf /ctx/system_files/. /`); this is the place for
  static config, not scripts.
- `system_files/usr/lib/sysusers.d/99-roberto.conf` — declarative user
  provisioning (systemd-sysusers format); add new users here, not via
  imperative `useradd` in a script.
- `image-template.env` — single source of truth for image name/tag/registry
  metadata; consumed by both `Justfile` and CI.
- `disk_config/*.toml` — BIB kickstart + Anaconda module config; `iso.toml`'s
  `%post` runs `bootc switch --mutate-in-place --transport registry
  ghcr.io/roberto286/fawos:latest` — update this if the image name/org changes.
- `.github/workflows/build.yml` — pushes+signs only on non-PR pushes to the
  default branch (see the `github.event_name != 'pull_request'` guard); PRs
  only build, never push/sign.
- `.github/workflows/build-disk.yml` — matrix over `disk-type: [qcow2,
  anaconda-iso]`, picks `disk_config/disk.toml` vs `disk_config/iso.toml`
  accordingly.
- `cosign.pub` / `cosign.key` (gitignored) — image signing keypair; `cosign.key`
  must never be committed (already in `.gitignore`).

## Runtime/Tooling Preferences

- **No Node/Bun/Python runtime** — this repo is Bash + `just` + `podman`
  (OCI/container tooling), not an application stack.
- Package manager inside the image: **`dnf5`** exclusively (Fedora Atomic
  default); do not introduce `rpm-ostree install` or `dnf` (v4) calls.
- Third-party packages come from **COPR**; enable immediately before install
  and disable immediately after unless the repo must stay live for later
  updates (see `avengemedia/danklinux`, left enabled deliberately).
- Container engine is **Podman** (not Docker) throughout `Justfile` and CI.
- `just --unstable --fmt` is the formatter/linter for the Justfile itself
  (`just check` / `just fix`); `shellcheck`/`shfmt` cover `*.sh` files
  (`just lint` / `just format`).

## Testing & QA

There is no unit/integration test framework — this is infrastructure code.
QA gates are:
1. `just check` — Justfile/`.just` syntax validation (CI step "Check Just Syntax").
2. `just lint` — `shellcheck` over every `*.sh` file.
3. `just build` — the image must build cleanly; the Containerfile's final
   `RUN bootc container lint` step is the authoritative correctness check for
   image contents/layout.
4. For behavioral changes to the desktop/kernel/display-manager setup, boot a
   VM to confirm: `just build-qcow2 && just run-vm-qcow2` (or `just spawn-vm`)
   and visually verify greetd → Hyprland login works.
5. CI (`build.yml`) re-runs `just check` and the full build on every PR before
   any push/signing occurs — treat a green PR build as the real acceptance gate.
