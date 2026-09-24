#!/bin/bash

# --- POWER MANAGEMENT: TUNED + TUNED-PPD (desktop + laptop) ---
# power-profiles-daemon NON va installato: confligge con tuned-ppd (già
# preinstallato nell'immagine base — Fedora ha reso tuned il daemon di
# default per la gestione power profile, sostituendo power-profiles-daemon;
# i due pacchetti forniscono entrambi "ppd-service" e non possono coesistere).
# tuned-ppd espone la stessa interfaccia D-Bus (net.hadess.PowerProfiles) di
# power-profiles-daemon, restando un drop-in replacement trasparente per
# strumenti/desktop che si aspettano l'API PPD.
dnf5 install -y tuned tuned-ppd
systemctl enable tuned-ppd.service

mkdir -p /usr/lib/systemd/system/multi-user.target.wants
ln -sf /usr/lib/systemd/system/fawos-power-default.service \
  /usr/lib/systemd/system/multi-user.target.wants/fawos-power-default.service

# --- FINE POWER MANAGEMENT ---
