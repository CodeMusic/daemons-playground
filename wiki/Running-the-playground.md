# Running the playground

## What it needs

- **DAEMONS beside it**: `~/Projects/DAEMONS` and `~/Projects/daemons-playground`, as DAEMONS' `setup.sh` arranges
  (it links this repository in as `DAEMONS/playground`). The ROMs are read from DAEMONS' `ROM RELEASE/`, so a release
  must have been built on this machine.
- **Python 3.8 or newer**, nothing to install, for the playground itself.
- **For the COMPANION tab**: daemons-companion beside DAEMONS (linked as `DAEMONS/companion`), `npm install` once in its
  `server/` and its `app/`, and Node 24. Without it the game still plays.

## Start it

```bash
./bindPlayground.sh
```

Then open `http://localhost:4740/`, or the tailnet address it prints to play from a phone. Nothing else needs to be
running.

| | |
|---|---|
| `./bindPlayground.sh --build` | DAEMONS' own `engineGba` build instead of the latest release, to try a change before it is released |
| `./bindPlayground.sh --port 8000` | another port |
| `./bindPlayground.sh --companion URL` | the COMPANION tab's site from somewhere else -- `http://localhost:8081/` is the Expo dev server's, to work on the companion and see each change at once |
| `./bindPlayground.sh --no-companion` | no companion of the playground's own |
| `./bindPlayground.sh --companion-port 4731` | the first of the four companions' ports |
| `DAEMONS_ROOT=/path/to/DAEMONS` | DAEMONS somewhere other than beside this repository |
| `COMPANION_ROOT=/path/to/daemons-companion` | the companion somewhere other than `DAEMONS/companion` |

## Who it answers

**Only this machine, a private network and the tailnet.** Anything else is refused before a byte is read. Keep it that
way: the ROMs run Nintendo's engine, and the playground exists to show the game to people on your own network.

## Its files

`data/` is ignored by git and is this machine's alone: the saves the browser posts (`data/saves/`), the companions'
databases (`data/companions/`), the export of the companion's site (`data/companion-site/`) and its log (`data/companion-site.log`), and each
companion's own log (`data/companions/<build>/server.log`).
