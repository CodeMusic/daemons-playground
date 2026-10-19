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
- **Download save**: the game's save as a `.sav` at any moment, for mGBA, Delta or a cart. The page also keeps the
  last one in your browser and offers it the next time you come back.

It always serves the **newest release**: the ROMs are read from DAEMONS' `ROM RELEASE/` each time a game starts.

## Running it

DAEMONS sits beside this repository (`~/Projects/DAEMONS` and `~/Projects/daemons-playground`), as its
`setup.sh` arranges, and links this one in as `DAEMONS/playground`.

```bash
./bindPlayground.sh
```

Then open `http://localhost:4740/`, or the tailnet address it prints to play from a phone. The COMPANION tab shows the
companion's site from the same host at port 8081: start it with `./companion/bindCompanion.sh app` from DAEMONS (the
site alone; the playground runs its own companions behind it), or point the tab elsewhere with `--companion URL`. The
playground's companions need daemons-companion beside DAEMONS (DAEMONS' `setup.sh` links it as `DAEMONS/companion`),
its server installed once (`npm install` in its `server/`), and Node 24.

| | |
|---|---|
| `./bindPlayground.sh --build` | DAEMONS' own `engineGba` build instead of the latest release, to try a change before it is released |
| `./bindPlayground.sh --port 8000` | another port |
| `./bindPlayground.sh --companion URL` | the COMPANION tab's site |
| `./bindPlayground.sh --no-companion` | no companion of the playground's own: the tab shows the site on its own server |
| `./bindPlayground.sh --companion-port 4731` | the first of the four companions' ports |
| `DAEMONS_ROOT=/path/to/DAEMONS` | DAEMONS somewhere other than beside this repository |
| `COMPANION_ROOT=/path/to/daemons-companion` | the companion somewhere other than `DAEMONS/companion` |

Python 3.8 or newer, nothing to install.

## What is not here, and why

**No ROM, and nothing of Nintendo's.** DAEMONS is built on pret's disassembly of a Nintendo game, so its ROMs are never
distributed. This repository holds only the page and its small server (and `data/`, ignored: the saves and the
companions' databases, this machine's alone); the ROMs are read from the DAEMONS checkout
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

## Keys

Arrows move, **Z** is A, **X** is B, **Enter** START, **V** SELECT, **Q** and **E** L and R: EmulatorJS's own, changed
with the controller button under the game.
