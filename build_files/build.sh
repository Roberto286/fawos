#!/bin/bash
set -ouex pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

cp -avf "/ctx/system_files"/. /

# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

# --- Fase 1: abilita tutti i repository ---
FEDORA_VERSION=$(rpm -E %fedora)
enable_persistent_repo "https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-${FEDORA_VERSION}.noarch.rpm"
enable_persistent_repo "https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-${FEDORA_VERSION}.noarch.rpm"
enable_repos "${SCRIPT_DIR}/repo.txt"
enable_repos "${SCRIPT_DIR}/temp_repo.txt"

# --- Fase 2: installa tutti i pacchetti dnf5 ---
install_packages "${SCRIPT_DIR}/packages.txt"

# Il kernel CachyOS richiede ancora bieszczaders/kernel-cachyos attiva (swap
# atomico + devel package): va eseguito qui, prima di disabilitare le COPR
# effimere.
source "${SCRIPT_DIR}/domains/kernel.sh"

# --- Fase 3: disabilita i repository temporanei ---
disable_repos "${SCRIPT_DIR}/temp_repo.txt"

# --- Fase 4: installa i Flatpak ---
flatpak remote-add --system --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
install_flatpaks "${SCRIPT_DIR}/flatpak.txt"

# --- Fase 5: abilita le unit systemd ---
enable_services "${SCRIPT_DIR}/services.txt"

# --- Fase 6: resto della logica per dominio (utenti, servizi, dotfiles, ...) ---
for domain in users desktop devtools containers power dotfiles context virtualization; do
  # shellcheck disable=SC1090
  source "${SCRIPT_DIR}/domains/${domain}.sh"
done
