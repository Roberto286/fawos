#!/bin/bash

# --- VIRTUALIZZAZIONE: QEMU/KVM + VIRT-MANAGER ---
install_packages "${SCRIPT_DIR}/packages/virtualization.txt"
systemctl enable libvirtd.service

# --- FINE VIRTUALIZZAZIONE ---
