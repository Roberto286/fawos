#!/bin/bash

# --- DEV TOOLING: MISE + LAZYGIT + LAZYDOCKER ---

# mise: installer ufficiale, ospitato sul CDN di GitHub invece del dominio corto
# mise.run (problemi DNS intermittenti riscontrati su rete self-hosted) — stesso
# script, alternativa confermata dal maintainer di mise stesso:
# https://github.com/jdx/mise/discussions/6970
mise_installed=0
for _mise_attempt in 1 2 3; do
  curl --retry 3 -fsSL https://github.com/jdx/mise/releases/latest/download/install.sh \
    | MISE_INSTALL_PATH=/usr/local/bin/mise sh && { mise_installed=1; break; }
  echo "AVVISO: installazione mise fallita (tentativo ${_mise_attempt}/3), riprovo tra 3s..." >&2
  sleep 3
done
[ "$mise_installed" -eq 1 ] || { echo "ERRORE: installazione mise fallita dopo 3 tentativi" >&2; exit 1; }

# lazygit / lazydocker: via COPR (stesso maintainer atim, pattern COPR standard)
enable_copr "atim/lazygit"
enable_copr "atim/lazydocker"
dnf5 install -y lazygit lazydocker
disable_copr "atim/lazygit"
disable_copr "atim/lazydocker"

mkdir -p /usr/lib/systemd/user/default.target.wants
ln -sf /usr/lib/systemd/user/mise-bootstrap.service \
  /usr/lib/systemd/user/default.target.wants/mise-bootstrap.service

# --- FINE DEV TOOLING ---
