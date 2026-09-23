#!/bin/bash
set -ouex pipefail

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

cp -avf "/ctx/system_files"/. /

source "${SCRIPT_DIR}/lib/common.sh"

for domain in users kernel desktop terminal devtools containers apps gpu gaming power; do
  source "${SCRIPT_DIR}/domains/${domain}.sh"
done
