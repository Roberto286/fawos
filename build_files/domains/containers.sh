# --- CONTAINER TOOLING: PODMAN + DISTROBOX ---
install_packages "${SCRIPT_DIR}/packages/containers.txt"

systemctl enable podman.socket

mkdir -p /usr/lib/systemd/user/default.target.wants
ln -sf /usr/lib/systemd/user/podman.socket \
  /usr/lib/systemd/user/default.target.wants/podman.socket

# --- FINE CONTAINER TOOLING ---
