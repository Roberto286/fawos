#!/bin/bash

# --- DOTFILES: CHEZMOI ---
# chezmoi già installato da build.sh (Fase 2)

mkdir -p /usr/lib/systemd/user/default.target.wants
ln -sf /usr/lib/systemd/user/chezmoi-bootstrap.service \
  /usr/lib/systemd/user/default.target.wants/chezmoi-bootstrap.service

# --- FINE DOTFILES ---
