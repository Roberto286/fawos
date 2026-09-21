# --- CONFIGURAZIONE KERNEL CACHYOS ---

# 1. Abilita il repository COPR di CachyOS
dnf5 -y copr enable bieszczaders/kernel-cachyos

# 2. Forza dracut a usare il filesystem del container anziché /tmp (evita os error 18)
mkdir -p /var/tmp/dracut-build
export TMPDIR=/var/tmp/dracut-build

# 3. Esegui lo SWAP atomico dei soli pacchetti reali esistenti nel COPR
# Rimpiazziamo il kernel stock Fedora con quello di CachyOS
dnf5 -y --setopt=protected_packages= \
        --setopt=protect_running_kernel=False \
        swap kernel kernel-cachyos --allowerasing

dnf5 -y --setopt=protected_packages= \
        --setopt=protect_running_kernel=False \
        swap kernel-core kernel-cachyos-core --allowerasing

dnf5 -y --setopt=protected_packages= \
        --setopt=protect_running_kernel=False \
        swap kernel-modules kernel-cachyos-modules --allowerasing

# 4. Installa i pacchetti di sviluppo corretti per CachyOS
dnf5 -y install kernel-cachyos-devel-matched

# 5. Pulizia della cartella temporanea e rimozione della variabile d'ambiente
rm -rf /var/tmp/dracut-build
unset TMPDIR

# 6. Disabilita il repository COPR per pulizia dei metadati
dnf5 -y copr disable bieszczaders/kernel-cachyos

# --- FINE CONFIGURAZIONE KERNEL ---

