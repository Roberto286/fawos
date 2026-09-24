#!/bin/bash

# --- PROVISIONING UTENTE ---

# Materializza l'account dichiarato in sysusers.d (idempotente)
systemd-sysusers /usr/lib/sysusers.d/99-roberto.conf

# Password impostata solo se il secret è stato passato al build (solo CI)
if [ -s /run/secrets/roberto_password ]; then
    echo "roberto:$(cat /run/secrets/roberto_password)" | chpasswd
else
    echo "AVVISO: secret 'roberto_password' assente — password roberto non impostata da questa build (normale per build locali)." >&2
fi

# --- FINE PROVISIONING UTENTE ---
