# --- DEV TOOLING: MISE + LAZYGIT + LAZYDOCKER ---

# mise: installer ufficiale (gestisce piattaforma/architettura/estrazione autonomamente).
# Retry: unica curl "grezza" a singolo host del build (dnf5/COPR altrove hanno già
# retry/failover su più mirror integrato) — sopravvive a blip DNS transitori dello
# stack di rete slirp4netns/pasta usato dai build podman rootless.
mise_installed=0
for _mise_attempt in 1 2 3; do
  curl -fsSL https://mise.run | MISE_INSTALL_PATH=/usr/local/bin/mise sh && { mise_installed=1; break; }
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
