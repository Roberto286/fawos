#!/bin/bash
set -ouex pipefail
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

# Copy the contents of system_files/ of the git repo to /
cp -avf "/ctx/system_files"/. /

source "${SCRIPT_DIR}/kernel.sh"
source "${SCRIPT_DIR}/dms.sh"

### Install packages

# Packages can be installed from any enabled yum repo on the image.
# RPMfusion repos are available by default in ublue main images
# List of rpmfusion packages can be found here:
# https://rpmfusion.org

# this installs a package from fedora repos
dnf5 install -y tmux

#### Example for enabling a System Unit File

systemctl enable podman.socket

# Installazione di Hyprland da COPR
dnf5 -y copr enable lionheartp/Hyprland
dnf5 -y install Hyprland 
dnf5 -y copr disable lionheartp/Hyprland

