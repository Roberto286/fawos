#!/bin/bash

# --- CONTEXT: AGENTS.md SEEDING ---
mkdir -p /usr/lib/systemd/user/default.target.wants
ln -sf /usr/lib/systemd/user/fawos-context-sync.service \
  /usr/lib/systemd/user/default.target.wants/fawos-context-sync.service

# --- FINE CONTEXT ---
