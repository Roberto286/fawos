#!/bin/bash

# --- DOTFILES: CHEZMOI ---
dnf5 install -y chezmoi

mkdir -p /usr/lib/systemd/user/default.target.wants
ln -sf /usr/lib/systemd/user/chezmoi-bootstrap.service \
  /usr/lib/systemd/user/default.target.wants/chezmoi-bootstrap.service

# --- FINE DOTFILES ---
