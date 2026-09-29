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

# Esegue un comando dnf5 con retry su fallimento di rete (3 tentativi, backoff
# 3s) — rete self-hosted con DNS intermittenti verso host esterni (COPR,
# GitHub, ...), stesso problema già visto e risolto per l'installer mise.
dnf5_retry() {
  local attempt
  for attempt in 1 2 3; do
    dnf5 "$@" && return 0
    echo "AVVISO: dnf5 $* fallito (tentativo ${attempt}/3), riprovo tra 3s..." >&2
    sleep 3
  done
  echo "ERRORE: dnf5 $* fallito dopo 3 tentativi" >&2
  exit 1
}

# COPR effimere: enable -> install -> disable nello stesso dominio
enable_copr() { dnf5_retry -y copr enable "$1"; }
disable_copr() { dnf5 -y copr disable "$1"; }

# Repo persistenti (es. RPM Fusion) — restano abilitate nell'immagine finale
enable_persistent_repo() {
  local url="$1"
  dnf5 install -y "$url"
}
