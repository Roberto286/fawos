#!/bin/bash

# --- CONFIGURAZIONE KERNEL CACHYOS ---
# Repo bieszczaders/kernel-cachyos già abilitata da build.sh (Fase 1) e
# disabilitata dopo questo script (Fase 3): qui solo swap + devel package.

# 1. Forza dracut a usare il filesystem del container anziché /tmp (evita os error 18)
mkdir -p /var/tmp/dracut-build
export TMPDIR=/var/tmp/dracut-build

# 3. Esegui lo SWAP atomico dei soli pacchetti reali esistenti nel COPR
# Rimpiazziamo il kernel stock Fedora con quello di CachyOS
# (dnf5_retry: gli stessi comandi toccano i metadati della COPR appena
# abilitata, soggetti allo stesso DNS intermittente di enable_copr sopra)
dnf5_retry -y --setopt=protected_packages= \
        --setopt=protect_running_kernel=False \
        swap kernel kernel-cachyos --allowerasing

dnf5_retry -y --setopt=protected_packages= \
        --setopt=protect_running_kernel=False \
        swap kernel-core kernel-cachyos-core --allowerasing

dnf5_retry -y --setopt=protected_packages= \
        --setopt=protect_running_kernel=False \
        swap kernel-modules kernel-cachyos-modules --allowerasing

# 4. Installa i pacchetti di sviluppo corretti per CachyOS
dnf5_retry -y install kernel-cachyos-devel-matched

# 5. Pulizia della cartella temporanea e rimozione della variabile d'ambiente
rm -rf /var/tmp/dracut-build
unset TMPDIR

# --- FINE CONFIGURAZIONE KERNEL ---

