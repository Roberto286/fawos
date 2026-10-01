#!/bin/bash

# --- CONTAINER TOOLING: PODMAN + DISTROBOX ---
# podman-compose, distrobox già installati da build.sh (Fase 2);
# podman.socket abilitato da build.sh (Fase 5) via services.txt

mkdir -p /usr/lib/systemd/user/default.target.wants
ln -sf /usr/lib/systemd/user/podman.socket \
  /usr/lib/systemd/user/default.target.wants/podman.socket

# --- FINE CONTAINER TOOLING ---
