#!/bin/bash
set -ouex pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

cp -avf "/ctx/system_files"/. /

# shellcheck source=lib/common.sh
source "${SCRIPT_DIR}/lib/common.sh"

for domain in users kernel desktop terminal devtools containers apps gpu gaming power security dotfiles context media virtualization; do
  # shellcheck disable=SC1090
  source "${SCRIPT_DIR}/domains/${domain}.sh"
done
