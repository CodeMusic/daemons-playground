# The COMPANION tab

**[daemons-companion](https://github.com/CodeMusic/daemons-companion)'s site, beside the game**: the daemon you carry,
its care, its routines, the CASINO, the LIBRARY and the rest, on **a companion of the playground's own**, fed the game
you are playing. The game pauses while you look. What the companion does:
[its wiki](https://github.com/CodeMusic/daemons-companion/wiki).

## Never your own companion

The playground runs **one companion for each build** -- CONTENT on port 4731, CONTEXT 4732, their DEBUG builds 4733 and
4734. Each is daemons-companion's own server, started the first time a game of that build opens the tab and stopped
with the playground. Each keeps its database in `data/companions/` and reads the save the browser posts to
`data/saves/`. Nothing here touches a companion on port 4730, its database or a save of yours.

## Sending a daemon

It works as it does with a cart and the app:

1. In the game, a daemon's menu offers **SEND**. A normal game needs a first SYNC to link the companion. The game
   saves.
2. Open **COMPANION**. The companion SYNCs that save, takes the daemon and writes it AWAY. The save it wrote goes back
   into the game, which starts again from it -- the game is closed while the companion edits its save.
3. Back on **GAME**, choose CONTINUE. The daemon is washed out in your party, and it is on the companion's TODAY and
   DAEMON pages, to feed, train and take on its routines.

Bringing it home is the same, the other way. A SYNC pressed in the companion's own site is taken back into the game
too.

## From a phone

It works the same over the tailnet. The companions listen only on the playground's machine; the site reaches the one for
your build through the playground's own server, at `/companion/<build>/` (told where by `?server=`). So a phone needs no
pairing -- and what only that machine may do (pairing a phone, opening the network, the file picker, the relay, Home
Assistant, the save's path) is refused there.

## The site it shows

The playground **exports the companion's site itself** (`npx expo export --platform web`, with Node 24) into
`data/companion-site/`, and serves it at `/companion-site/`. So the tab needs no Expo dev server, and a phone loads one
minified bundle of about 2 MB, once.

It is exported again only when the companion has changed -- its commit, or anything uncommitted in its `app/`,
`server/src` or `server/data`. The playground looks as it starts and, at most every 30 seconds, as pages ask. The export
runs in the background (a few seconds once Metro's cache is warm, about a minute the first time), and the one before is
served until it is done. One that fails keeps the one before, and is not tried again until the companion changes.

**To work on the companion's site** and see each change at once, run its Expo dev server
(`./companion/bindCompanion.sh app` from DAEMONS) and start the playground with `--companion http://localhost:8081/`.
