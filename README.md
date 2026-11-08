# fawos &nbsp; [![bluebuild build badge](https://github.com/roberto286/fawos/actions/workflows/build.yml/badge.svg)](https://github.com/roberto286/fawos/actions/workflows/build.yml)

Personal Fedora bootc image: niri + DankMaterialShell, CachyOS kernel, BTRFS with home snapshots.

## Installation

> [!WARNING]  
> [This is an experimental feature](https://www.fedoraproject.org/wiki/Changes/OstreeNativeContainerStable), try at your own discretion.

To rebase an existing atomic Fedora installation to the latest build:

- First rebase to the unsigned image, to get the proper signing keys and policies installed:
  ```
  rpm-ostree rebase ostree-unverified-registry:ghcr.io/roberto286/fawos:latest
  ```
- Reboot to complete the rebase:
  ```
  systemctl reboot
  ```
- Then rebase to the signed image, like so:
  ```
  rpm-ostree rebase ostree-image-signed:docker://ghcr.io/roberto286/fawos:latest
  ```
- Reboot again to complete the installation
  ```
  systemctl reboot
  ```

The `latest` tag tracks the latest fawos build. The image follows Fedora **45**. A major bump is a manual edit of `image-version` in `recipes/recipe.yml`, done once the CachyOS COPR supports the new release. If the COPR lags, the build fails instead of falling back to the Fedora kernel, and existing installations remain on the last successfully published image.

## Updates

Run the following command from your normal desktop user account, **without prefixing it with `sudo`**:

```bash
fawos-update
```

The command updates:

- The system image with `sudo bootc upgrade`, including the kernel, RPM packages, and the mise/chezmoi executables. This downloads the latest published fawos image; it does not rebuild it or run DNF on the host.
- Flatpak applications and runtimes in both the default system installation and the current user's installation. Only the system installation uses sudo.
- Dotfiles through the existing `chezmoi-update.service` user service. The chezmoi policy is `skip`: dotfiles you changed locally are never overwritten, the service reports a failure (desktop notification), and `fawos-update` lists them. Save with `chezmoi re-add`, or discard with `chezmoi apply --force <file>`.
- Tools in the user's global mise configuration with `mise upgrade --global --yes`. Version ranges and exact pins are respected; project configurations and project lockfiles are not changed, regardless of the current directory.

Failed steps are listed at the end and the command exits with status 1; other steps are still attempted. Interrupting the command stops it. Successful updates are not rolled back when another step fails.

There is no automatic reboot. Reboot manually to activate any staged system image; Flatpak, dotfile, and mise updates apply separately. Automatic update timers from the base image remain enabled. Firmware flashing and updates inside Distrobox or other containers are not performed.

## Kernel

fawos replaces the stock Fedora kernel with `kernel-cachyos` from the [CachyOS Fedora COPR](https://github.com/CachyOS/copr-linux-cachyos). The replacement happens during the image build, followed by initramfs regeneration. Kernel updates arrive through new fawos images; no host-side kernel override is required.

Kernel installation and initramfs regeneration set `DRACUT_NO_XATTR=1` to avoid unsupported extended-attribute copies in container builds. This does not disable SELinux.

- The standard CachyOS kernel requires an **x86-64-v3** CPU.
- **Secure Boot:** this recipe does not sign the replacement kernel. Before booting the image, either sign the kernel with your own trusted key or disable Secure Boot. Disabling Secure Boot reduces protection against boot-time tampering. The `signing` module configures container signature verification, not kernel signing.
- NVIDIA and other out-of-tree modules must be built for the exact CachyOS kernel version; Fedora-kernel modules cannot be reused.
- The image persistently enables the SELinux boolean `domain_kernel_load_modules`, as required by the CachyOS Fedora port, without disabling SELinux.

Before deploying a new kernel, test booting the image in a VM and retain a known-good deployment for rollback. After boot, `uname -r` should report a CachyOS kernel.

## ISO

`.github/workflows/build-iso.yml` builds an Anaconda installer ISO from the published image on the 1st of each month (or via manual dispatch) and uploads it as a workflow artifact kept for 7 days.

## Filesystem

The installer has no filesystem picker; the layout comes from Anaconda's `fedora` profile, which provisions **BTRFS** (`zstd:1` compression, subvolumes for `/` and `/home`, `/boot` on ext4). The manual install path is kept consistent by `/usr/lib/bootc/install/50-fawos.toml` in the image, so `bootc install to-disk` also defaults to BTRFS. Enable disk encryption in Anaconda on laptops; the image does not enforce it.

### Home directories

Homes live on `/var/home`, with `/home` as a symlink to it (the ostree layout).
`$HOME` is whatever `/etc/passwd` says, so an account created at install time can
end up with the legacy `/home/<user>` spelling even though it is the same
directory. `fawos-normalize-home.service` rewrites those entries to
`/var/home/<user>` on boot; after the first run it is a no-op.

```bash
getent passwd roberto   # -> /var/home/roberto
```

### Snapshots

`snapper` timeline snapshots of the home subvolume (`/var/home`) are preconfigured
(6 hourly, 7 daily, 4 weekly, 6 monthly; config in `/etc/snapper/configs/home`).
`fawos-snapper-home.service` creates the `.snapshots` subvolume on first boot.

```bash
sudo snapper -c home list
sudo snapper -c home undochange <pre#>..<post#>
```

This needs `/var/home` to be its own btrfs subvolume, which is the layout the ISO
produces. A bare `bootc install to-disk` puts it inside the root subvolume; there
the setup service logs and leaves snapshots off.

The OS itself does not need snapshots: bootc deployments are atomic and
`bootc rollback` goes back to the previous one. The root subvolume is deliberately
not snapshotted, because that would pin the ostree object store.

## Verification

These images are signed with [Sigstore](https://www.sigstore.dev/)'s [cosign](https://github.com/sigstore/cosign). You can verify the signature by downloading the `cosign.pub` file from this repo and running the following command:

```bash
cosign verify --key cosign.pub ghcr.io/roberto286/fawos
```
