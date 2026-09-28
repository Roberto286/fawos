if status is-interactive
    if not test -f ~/.local/state/fawos-welcome-shown
        set_color cyan
        echo "Benvenuto su fawos."
        set_color normal
        echo "  - Documentazione di sistema: cat ~/AGENTS.md"
        echo "  - Scegli/cambia il tuo agente AI: fawos-agent --choose"
        echo "  - Aggiorna il sistema: fawos-update"
        echo
        mkdir -p ~/.local/state
        touch ~/.local/state/fawos-welcome-shown
    end
end
