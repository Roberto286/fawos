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
# enable_copr ritenta 3 volte (rete self-hosted con DNS intermittenti verso
# host esterni, stesso problema già visto e risolto per l'installer mise) —
# copr enable stesso richiede rete verso copr.fedorainfracloud.org per
# risolvere l'URL del repo, non è un'operazione locale.
enable_copr() {
  local copr="$1"
  local attempt
  for attempt in 1 2 3; do
    dnf5 -y copr enable "$copr" && return 0
    echo "AVVISO: enable_copr ${copr} fallito (tentativo ${attempt}/3), riprovo tra 3s..." >&2
    sleep 3
  done
  echo "ERRORE: enable_copr ${copr} fallito dopo 3 tentativi" >&2
  exit 1
}
disable_copr() { dnf5 -y copr disable "$1"; }

# Repo persistenti (es. RPM Fusion) — restano abilitate nell'immagine finale
enable_persistent_repo() {
  local url="$1"
  dnf5 install -y "$url"
}
