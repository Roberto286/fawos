# fawos &nbsp; [![bluebuild build badge](https://github.com/roberto286/fawos/actions/workflows/build.yml/badge.svg)](https://github.com/roberto286/fawos/actions/workflows/build.yml)

See the [BlueBuild docs](https://blue-build.org/how-to/setup/) for quick setup instructions for setting up your own repository based on this template.

After setup, it is recommended you update this README to describe your custom image.

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

The `latest` tag tracks the latest fawos build. The recipe also uses the base image's `latest` tag, so new builds automatically follow Fedora major releases. If the CachyOS COPR does not support the new Fedora release yet, the build fails instead of falling back to the Fedora kernel. Existing installations remain on the last successfully published image until a new build succeeds.

## Updates

Run the following command from your normal desktop user account, **without prefixing it with `sudo`**:

```bash
fawos-update
```

The command updates:

- The system image with `sudo bootc upgrade`, including the kernel, RPM packages, and the mise/chezmoi executables. This downloads the latest published fawos image; it does not rebuild it or run DNF on the host.
- Flatpak applications and runtimes in both the default system installation and the current user's installation. Only the system installation uses sudo.
- Dotfiles through the existing `chezmoi-update.service` user service, preserving its configured conflict policy. The current `replace` policy overwrites local changes to managed dotfiles.
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

If build on Fedora Atomic, you can generate an offline ISO with the instructions available [here](https://blue-build.org/how-to/generate-iso/#_top). These ISOs cannot unfortunately be distributed on GitHub for free due to large sizes, so for public projects something else has to be used for hosting.

## Verification

These images are signed with [Sigstore](https://www.sigstore.dev/)'s [cosign](https://github.com/sigstore/cosign). You can verify the signature by downloading the `cosign.pub` file from this repo and running the following command:

```bash
cosign verify --key cosign.pub ghcr.io/roberto286/fawos
```
