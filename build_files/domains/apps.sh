#!/bin/bash

# --- APP GUI: FIREFOX & BITWARDEN (FLATPAK, BAKED A BUILD-TIME) ---
dnf5 install -y flatpak
flatpak remote-add --system --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --system -y flathub org.mozilla.firefox com.bitwarden.desktop

# --- FINE APP GUI ---
