#!/bin/bash

# --- DEV TOOLING: MISE + LAZYGIT + LAZYDOCKER ---

# mise: installer ufficiale, ospitato sul CDN di GitHub invece del dominio corto
# mise.run (problemi DNS intermittenti riscontrati su rete self-hosted) — stesso
# script, alternativa confermata dal maintainer di mise stesso:
# https://github.com/jdx/mise/discussions/6970
# Installato in /usr/bin (non /usr/local/bin: su Fedora Atomic/Silverblue
# /usr/local è un symlink verso /var/usrlocal, che a build-time non esiste
# ancora — mkdir fallisce con "File exists" sul symlink stesso).
mise_installed=0
for _mise_attempt in 1 2 3; do
  curl --retry 3 -fsSL https://github.com/jdx/mise/releases/latest/download/install.sh \
    | MISE_INSTALL_PATH=/usr/bin/mise sh && { mise_installed=1; break; }
  echo "AVVISO: installazione mise fallita (tentativo ${_mise_attempt}/3), riprovo tra 3s..." >&2
  sleep 3
done
[ "$mise_installed" -eq 1 ] || { echo "ERRORE: installazione mise fallita dopo 3 tentativi" >&2; exit 1; }

# lazygit / lazydocker: già installati da build.sh (Fase 2) via packages.txt
# (COPR atim/lazygit, atim/lazydocker in temp_repo.txt)
# fawos-agent: lazy picker tra CLI agent AI (omp/claude/opencode/codex/pi).
# Backend mise esatto per ciascun agente varia (npm:/aqua:/github release/
# installer proprietario) — installati on-demand dallo stub stesso al primo
# uso reale, non pre-installati qui: nessuno dei cinque è garantito
# risolvibile da un unico pattern mise, e pre-installarli tutti e cinque a
# build-time gonfierebbe l'immagine per strumenti che potresti non usare mai.

mkdir -p /usr/lib/systemd/user/default.target.wants
ln -sf /usr/lib/systemd/user/mise-bootstrap.service \
  /usr/lib/systemd/user/default.target.wants/mise-bootstrap.service

# --- FINE DEV TOOLING ---
