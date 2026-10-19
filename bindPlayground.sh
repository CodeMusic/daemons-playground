#!/usr/bin/env bash
# The DAEMONS playground: the game in a browser, the companion beside it, what's new in each release.
#
#   ./bindPlayground.sh                 the latest ROM RELEASE, on port 4740
#   ./bindPlayground.sh --build         DAEMONS' engineGba build instead
#   ./bindPlayground.sh --port 8000
#   ./bindPlayground.sh --companion URL the COMPANION tab's site (default: the page's own host, port 8081)
#   ./bindPlayground.sh --no-companion  no companion of the playground's own: the tab shows its site's own server
#   ./bindPlayground.sh --companion-port 4731   the first of its own companions' four ports (4731-4734)
#
# It reads the ROMs from DAEMONS beside this repository (../DAEMONS, or $DAEMONS_ROOT) and answers only this machine,
# a private network and the tailnet. The COMPANION tab is a companion of the playground's own, one for each build,
# started when a game of that build first asks for it -- daemons-companion's server (DAEMONS/companion, or
# $COMPANION_ROOT) with its own database and the browser's save, under data/. Ctrl-C stops it and them.
set -euo pipefail
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")")"
case "${1:-}" in -h|--help|help) sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;; esac
exec python3 server/playground.py "$@"
