# --- DEV TOOLING: MISE + LAZYGIT + LAZYDOCKER ---

# mise: installer ufficiale (gestisce piattaforma/architettura/estrazione autonomamente)
curl -fsSL https://mise.run | MISE_INSTALL_PATH=/usr/local/bin/mise sh

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
