#!/bin/bash

# --- GAMING: RPM FUSION (persistente) + STEAM + LUTRIS + GAMEMODE/MANGOHUD ---
FEDORA_VERSION=$(rpm -E %fedora)
enable_persistent_repo "https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-${FEDORA_VERSION}.noarch.rpm"
enable_persistent_repo "https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-${FEDORA_VERSION}.noarch.rpm"

install_packages "${SCRIPT_DIR}/packages/gaming.txt"

# --- FINE GAMING ---
