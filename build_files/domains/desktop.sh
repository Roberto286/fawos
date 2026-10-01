#!/bin/bash

# --- DESKTOP: GREETD + DMS + HYPRLAND ---
# Pacchetti (dms, dms-greeter, greetd, Hyprland, satty, ghostty, ...) già
# installati da build.sh (Fase 2) via packages.txt; avengemedia/danklinux
# già abilitata e lasciata attiva da repo.txt. Qui solo config/symlink.

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

# --- BRANDING: PLYMOUTH ---
# Stesso workaround TMPDIR di kernel.sh: dracut non deve scrivere in /tmp
# nell'ambiente di build.
mkdir -p /var/tmp/dracut-build
export TMPDIR=/var/tmp/dracut-build
plymouth-set-default-theme fawos
rm -rf /var/tmp/dracut-build
unset TMPDIR

# --- FINE DESKTOP ---
