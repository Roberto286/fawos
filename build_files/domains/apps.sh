#!/bin/bash

# --- APP GUI: FIREFOX & THUNDERBIRD & BITWARDEN & LIBREOFFICE & FLATSEAL (FLATPAK) + STACK KDE (RPM) ---
dnf5 install -y flatpak
flatpak remote-add --system --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --system -y flathub org.mozilla.firefox org.mozilla.Thunderbird com.bitwarden.desktop org.libreoffice.LibreOffice com.github.tchx84.Flatseal

dnf5 install -y qalculate-gtk ark okular gwenview

# --- FINE APP GUI ---
