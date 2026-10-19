# daemons-playground

**An all-in-one harness to demo and beta test [DAEMONS](https://github.com/CodeMusic/DAEMONS)**, the whole game and
everything around it, from one URL.

Open the page, choose **CONTENT** or **CONTEXT** (and the **DEBUG** build, if you want its kit), start a new game or
continue from a `.sav`, and play it right there in the browser: on a Mac with the keyboard, on a phone with the buttons
on the screen. Beside the game:

- **COMPANION**: [daemons-companion](https://github.com/CodeMusic/daemons-companion)'s site in a tab, the daemon you
  carry, its care, the routines and the CASINO. The game pauses while you look.
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

Then open `http://localhost:4740/`, or the tailnet address it prints to play from a phone. The COMPANION tab expects the
companion's site on the same host at port 8081 (`./bindCompanion.sh` in daemons-companion). Point it elsewhere with
`--companion URL`.

| | |
|---|---|
| `./bindPlayground.sh --build` | DAEMONS' own `engineGba` build instead of the latest release, to try a change before it is released |
| `./bindPlayground.sh --port 8000` | another port |
| `./bindPlayground.sh --companion URL` | the COMPANION tab's site |
| `DAEMONS_ROOT=/path/to/DAEMONS` | DAEMONS somewhere other than beside this repository |

Python 3.8 or newer, nothing to install.

## What is not here, and why

**No ROM, and nothing of Nintendo's.** DAEMONS is built on pret's disassembly of a Nintendo game, so its ROMs are never
distributed. This repository holds only the page and its small server; the ROMs are read from the DAEMONS checkout
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

## Keys

Arrows move, **Z** is A, **X** is B, **Enter** START, **V** SELECT, **Q** and **E** L and R: EmulatorJS's own, changed
with the controller button under the game.
