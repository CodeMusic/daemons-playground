# daemons-playground

**An all-in-one harness to demo and beta test [DAEMONS](https://github.com/CodeMusic/DAEMONS)**, the whole game and
everything around it, from one URL.

Open the page, choose **CONTENT** or **CONTEXT** (and the **DEBUG** build, if you want its kit), start a new game or
continue from a `.sav`, and play it right there in the browser: on a Mac with the keyboard, on a phone with the buttons
on the screen. Beside the game:

- **COMPANION**: [daemons-companion](https://github.com/CodeMusic/daemons-companion)'s site in a tab, the daemon you
  carry, its care, the routines and the CASINO -- on **a companion of the playground's own**, fed the game you are
  playing. **SEND** a daemon in the game, open the tab, and it is there. The game pauses while you look.
- **WHAT'S NEW**: each release's notes, newest first, every engine and design change linked to its commit. If a newer
  release lands while you play, the page says so.
- **HELP**: how to play, how to use the companion (SEND, SYNC, care, CALL HOME), and where else a daemon can live --
  the companion's iPhone app and the LilyGO and M5Stack boards. It is on the start page too.
- **Download save**: the game's save as a `.sav` at any moment, for mGBA, Delta or a cart. The page also keeps the
  last one in your browser and offers it the next time you come back.

It always serves the **newest release**: the ROMs are read from DAEMONS' `ROM RELEASE/` each time a game starts.

## Running it

DAEMONS sits beside this repository (`~/Projects/DAEMONS` and `~/Projects/daemons-playground`), as its
`setup.sh` arranges, and links this one in as `DAEMONS/playground`.

```bash
./bindPlayground.sh
```

Then open `http://localhost:4740/`, or the tailnet address it prints to play from a phone. Nothing else needs to be
running: the COMPANION tab's site is the playground's own too (see [The companion's site](#the-companions-site)). The
companion needs daemons-companion beside DAEMONS (DAEMONS' `setup.sh` links it as `DAEMONS/companion`), installed once
(`npm install` in its `server/` and its `app/`), and Node 24.

| | |
|---|---|
| `./bindPlayground.sh --build` | DAEMONS' own `engineGba` build instead of the latest release, to try a change before it is released |
| `./bindPlayground.sh --port 8000` | another port |
| `./bindPlayground.sh --companion URL` | the COMPANION tab's site, instead of the playground's own export of it: `http://localhost:8081/` is the Expo dev server's (`./companion/bindCompanion.sh app`), to work on the companion and see it at once |
| `./bindPlayground.sh --no-companion` | no companion of the playground's own: the tab shows the site on its own server |
| `./bindPlayground.sh --companion-port 4731` | the first of the four companions' ports |
| `DAEMONS_ROOT=/path/to/DAEMONS` | DAEMONS somewhere other than beside this repository |
| `COMPANION_ROOT=/path/to/daemons-companion` | the companion somewhere other than `DAEMONS/companion` |

Python 3.8 or newer, nothing to install.

## What is not here, and why

**No ROM, and nothing of Nintendo's.** DAEMONS is built on pret's disassembly of a Nintendo game, so its ROMs are never
distributed. This repository holds only the page and its small server (and `data/`, ignored: the saves, the
companions' databases and the export of the companion's site, this machine's alone); the ROMs are read from the DAEMONS checkout
beside it, on the machine that built them. **The server answers only that machine, a private network and the
tailnet**, and refuses anything else before a byte is read. Keep it that way: the playground is for demos and beta
testing among the people on your own network, never a public site.

**No emulator either.** The game runs on [EmulatorJS](https://emulatorjs.org) (GPL-3.0) and its mGBA core, loaded from
EmulatorJS's own CDN, version 4.2.3, when a game starts.

## How the save is kept

EmulatorJS keeps a game's save in the browser while it runs but lets it go when the page is left, so the page keeps its
own copy. It checks the game's save every five seconds and whenever the page is hidden or closed, and stores it in the
browser's IndexedDB under the build's name whenever it has changed. A `.sav` you choose at the start replaces it. With
none chosen, the kept one is offered (continue it, download it, or start a new game) rather than silently continued or
lost. A saved game is 128 KB; mGBA's 131,088-byte files, with its clock after the flash, load as they are.

## The companion beside the game

The COMPANION tab never shows your own companion. The playground runs **one of its own for each build** -- CONTENT on
port 4731, CONTEXT 4732, their DEBUG builds 4733 and 4734 -- each daemons-companion's own server, started the first
time a game of that build opens the tab and stopped with the playground. Each keeps its database in `data/companions/`
and reads the save in `data/saves/`, which is the browser's: the page posts the game's save there whenever it changes.
Nothing here touches the companion on port 4730, its database or a save of yours.

**Sending a daemon** works as it does with a cart and the app. In the game, a daemon's menu offers SEND (a DEBUG game's
kit has the companion linked already; a normal one needs a first SYNC). The game saves. Open COMPANION: the companion
SYNCs that save, takes the daemon and writes it AWAY, and the save it wrote goes back into the game, which starts again
from it (the game is closed while the app edits its save). Back on GAME, choose CONTINUE: the daemon is washed out in
the party, and it is on the companion's TODAY and DAEMON pages, to feed, train and take on its routines. Bringing it
home is the same, the other way. A SYNC pressed in the companion's own site is taken back into the game too.

**From a phone** it works the same way over the tailnet. The companions listen only on the Mac; the companion's site
reaches the one for your build through the playground's server, at `/companion/<build>/` (it is told where by
`?server=`). So a phone needs no pairing, and what only the Mac may do (pairing a phone, opening the network, the file
picker, the relay, Home Assistant, the save's path) is refused there.

**A new game** puts the old save aside (`data/saves/*.before-new-game.sav`). A companion already married to another
game says so and offers to start fresh; the old one is kept aside as `data/companions/<build>.before`.

**One companion per build, for everyone.** Two people playing the same build on one playground at once share its save
and its companion, and each one's save replaces the other's. For a beta test with several people at once, give each a
different build, or a playground of their own.

## The companion's site

The COMPANION tab shows daemons-companion's own site, **exported by the playground and served by it**: as it starts,
it runs `npx expo export --platform web` in `DAEMONS/companion/app` (with Node 24) into `data/companion-site/`, and the
tab opens it at `/companion-site/` on the playground's own address, told by `?server=` to use the playground's
companion. So the tab needs no Expo dev server, and a phone on the tailnet loads one minified bundle (about 2 MB, once:
its name changes with what is in it) instead of a development build.

It is exported again only when the companion has changed since the last export -- its HEAD, or anything uncommitted
in its `app/`, `server/src` or `server/data`, which the site is built from. The playground looks as it starts and,
at most every 30 seconds, as pages ask after it; the export runs in the background (a few seconds once Metro's cache
is warm, about a minute the first time) and the one before is served until it is done. The commit it was made from is
in `data/companion-site.json`, the export's output in `data/companion-site.log`. An export that fails keeps the one before, and is not tried again until the companion
changes.

The export names its files from the root (`/_expo/…`, `/assets/…`: the app sets no `baseUrl`), so the playground serves
those two folders from it as well; nothing of the playground's own lives there.

**To work on the companion's site** and see each change at once, run the Expo dev server
(`./companion/bindCompanion.sh app` from DAEMONS) and start the playground with `--companion http://localhost:8081/`.
If the playground cannot export the site at all (no `npm install` in `app/`, no Node 24) and has never exported it, the
tab falls back to that dev server on the page's own host, port 8081, and says why when nothing answers there.

## Keys

Arrows move, **X** is A, **Z** is B (as in mGBA: EmulatorJS's own default is the other way round), **Enter** START,
**V** SELECT, **Q** and **E** L and R. Change them with the controller button under the game; a mapping you chose is
kept. On a phone, the buttons on the screen, laid out as on a GBA.
