#!/bin/bash

# Installa i pacchetti elencati in un file (un pkg per riga, '#' per commenti, righe vuote ignorate)
install_packages() {
  local file="$1"
  local pkgs=()
  while IFS= read -r line; do
    line="${line%%#*}"
    line="$(echo "$line" | xargs)"
    [[ -z "$line" ]] && continue
    pkgs+=("$line")
  done < "$file"
  dnf5 install -y "${pkgs[@]}"
}

# COPR effimere: enable -> install -> disable nello stesso dominio
enable_copr() { dnf5 -y copr enable "$1"; }
disable_copr() { dnf5 -y copr disable "$1"; }

# Repo persistenti (es. RPM Fusion) — restano abilitate nell'immagine finale
enable_persistent_repo() {
  local url="$1"
  dnf5 install -y "$url"
}
