#!/usr/bin/env bash
# The DAEMONS playground: the game in a browser, the companion beside it, what's new in each release.
#
#   ./bindPlayground.sh                 the latest ROM RELEASE, on port 4740
#   ./bindPlayground.sh --build         DAEMONS' engineGba build instead
#   ./bindPlayground.sh --port 8000
#   ./bindPlayground.sh --companion URL the COMPANION tab's site (default: its own export; http://localhost:8081/ is Metro's)
#   ./bindPlayground.sh --no-companion  no companion of the playground's own: the tab shows its site's own server
#   ./bindPlayground.sh --companion-port 4731   the first of its own companions' four ports (4731-4734)
#   ./bindPlayground.sh always          keep it running: started at login, started again if it stops (a login agent)
#   ./bindPlayground.sh never           stop doing that
#
# It reads the ROMs from DAEMONS beside this repository (../DAEMONS, or $DAEMONS_ROOT) and answers only this machine,
# a private network and the tailnet. The COMPANION tab is a companion of the playground's own, one for each build,
# started when a game of that build first asks for it -- daemons-companion's server (DAEMONS/companion, or
# $COMPANION_ROOT) with its own database and the browser's save, under data/. Its site is the playground's own as well:
# exported from the companion's app (expo export, Node 24) into data/companion-site/ as this starts, and again whenever
# the companion has changed -- no Expo dev server needed. Ctrl-C stops it and them.
set -euo pipefail
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || echo "${BASH_SOURCE[0]}")")"
case "${1:-}" in -h|--help|help) sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;; esac

# -- always / never: the playground as a login agent (2026-10-28: it had stopped, and a tester's link went nowhere).
# launchd starts it at login and again if it stops; its output goes to data/playground.log, where a tester's device
# reports what went wrong. The PATH is this shell's python3 and Node 24 (the companions and the site's export need it).
# It does not keep the Mac awake: the playground answers while the Mac does.
AGENT="$HOME/Library/LaunchAgents/ca.codemusic.daemons-playground.plist"
if [[ "${1:-}" == always ]]; then
  shift
  [[ $(uname -s) == Darwin ]] || { echo "bindPlayground: 'always' is a Mac login agent" >&2; exit 64; }
  mkdir -p data "$(dirname "$AGENT")"
  py="$(dirname "$(command -v python3)")"
  args=""; for a in "$@"; do args+="<string>$a</string>"; done   # what it is started with, e.g. --build
  cat > "$AGENT" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>ca.codemusic.daemons-playground</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$PWD/bindPlayground.sh</string>$args</array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>ThrottleInterval</key><integer>30</integer>
  <key>StandardOutPath</key><string>$PWD/data/playground.log</string>
  <key>StandardErrorPath</key><string>$PWD/data/playground.log</string>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>$py:/opt/homebrew/opt/node@24/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string></dict>
</dict>
</plist>
PLIST
  plutil -lint "$AGENT" >/dev/null
  launchctl bootout "gui/$(id -u)" "$AGENT" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$AGENT"
  echo "bindPlayground: it now runs whenever you are logged in, and starts again if it stops."
  echo "                If one was already running in a terminal, stop that one: this takes over within 30 seconds."
  echo "                Log: data/playground.log   Undo: ./bindPlayground.sh never"
  exit 0
fi
if [[ "${1:-}" == never ]]; then
  launchctl bootout "gui/$(id -u)" "$AGENT" 2>/dev/null || true
  rm -f "$AGENT"
  echo "bindPlayground: it no longer starts by itself. Start it with ./bindPlayground.sh when you want it."
  exit 0
fi

exec python3 server/playground.py "$@"
