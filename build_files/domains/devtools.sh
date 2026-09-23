# --- DEV TOOLING: MISE + LAZYGIT + LAZYDOCKER ---

# mise: binario dall'ultima release GitHub (pattern asset da verificare contro le release reali di jdx/mise)
install_github_release "jdx/mise" 'mise-v[0-9.]+-linux-x64$' /usr/local/bin/mise

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
