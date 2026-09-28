#!/bin/bash

# --- STACK GRAFICO AMD (RDNA2 baseline, RX 6700XT) ---
install_packages "${SCRIPT_DIR}/packages/gpu.txt"

# --- CORECTRL: overclock/undervolt GUI, nessun profilo baked ---
dnf5 install -y corectrl
