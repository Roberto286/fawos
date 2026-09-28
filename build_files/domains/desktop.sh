#!/bin/bash

# --- DESKTOP: GREETD + DMS + HYPRLAND ---

dnf5 -y copr enable avengemedia/danklinux

dnf5 -y install dms dms-greeter greetd

mkdir -p /etc/greetd

if [ -d "/etc/greetd" ]; then
    chmod 755 /etc/greetd
    if [ -f "/etc/greetd/config.toml" ]; then
        chmod 644 "/etc/greetd/config.toml"
    fi
fi

# Cambia il Display Manager predefinito a livello di sistema
if [ -L /etc/systemd/system/display-manager.service ]; then
    rm /etc/systemd/system/display-manager.service
fi
ln -s /usr/lib/systemd/system/greetd.service /etc/systemd/system/display-manager.service

# Abilita l'avvio automatico di DMS a livello utente
mkdir -p /usr/lib/systemd/user/hyprland.service.wants
ln -s /usr/lib/systemd/user/dms.service /usr/lib/systemd/user/hyprland.service.wants/dms.service

install_packages "${SCRIPT_DIR}/packages/desktop.txt"

# Installazione di Hyprland + resto dell'ecosistema hyprwm da COPR
# (consolidata qui da build.sh; hyprlauncher/hypridle/hyprlock/hyprsunset/
# gpu-screen-recorder confermati presenti nella stessa COPR)
enable_copr "lionheartp/Hyprland"
dnf5 -y install Hyprland hyprlauncher hypridle hyprlock hyprsunset gpu-screen-recorder
disable_copr "lionheartp/Hyprland"

# satty: annotazione screenshot, COPR upstream-maintained (mineiro/satty-rpms)
enable_copr "mineiro/satty"
dnf5 -y install satty
disable_copr "mineiro/satty"

# ghostty: terminale di default, COPR raccomandata da ghostty.org stesso
enable_copr "scottames/ghostty"
dnf5 -y install ghostty
disable_copr "scottames/ghostty"

# --- FINE DESKTOP ---
