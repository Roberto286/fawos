#!/bin/bash

# --- POWER MANAGEMENT: power-profiles-daemon + tuned-ppd (desktop + laptop) ---
dnf5 install -y power-profiles-daemon tuned tuned-ppd
systemctl enable power-profiles-daemon.service

mkdir -p /usr/lib/systemd/system/multi-user.target.wants
ln -sf /usr/lib/systemd/system/fawos-power-default.service \
  /usr/lib/systemd/system/multi-user.target.wants/fawos-power-default.service

# --- FINE POWER MANAGEMENT ---
