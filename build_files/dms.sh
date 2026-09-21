dnf5 -y copr enable avengemedia/danklinux

dnf5 -y install dms dms-greeter greetd

mkdir -p /etc/greetd

 if [ -d "/etc/greetd" ]; then
    chmod 755 /etc/greetd
    if [ -f "/etc/greetd/config.toml" ]; then
        chmod 644 /etc/greetd/config.toml
    fi
fi

# 4. Cambia il Display Manager predefinito a livello di sistema
if [ -L /etc/systemd/system/display-manager.service ]; then
    rm /etc/systemd/system/display-manager.service
fi
ln -s /usr/lib/systemd/system/greetd.service /etc/systemd/system/display-manager.service

# 5. Abilita l'avvio automatico di DMS a livello utente (se usi Niri o servizi dedicati)
mkdir -p /usr/lib/systemd/user/hyprland.service.wants
ln -s /usr/lib/systemd/user/dms.service /usr/lib/systemd/user/hyprland.service.wants/dms.service
