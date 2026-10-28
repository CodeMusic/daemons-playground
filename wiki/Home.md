# DAEMONS playground

**The game in a browser, for demos and beta tests**, from one URL. Choose an edition, start a new game or continue from
a `.sav`, and play [DAEMONS](https://github.com/CodeMusic/DAEMONS) right there -- on a Mac with the keyboard, on a phone
with the buttons on the screen. Beside the game, in tabs: the [companion](https://github.com/CodeMusic/daemons-companion)
with the daemons you SEND, each release's notes, and help.

It is the browser's way into what the companion's app does on an iPhone or iPad: the game and the companion together.
([The one app](https://github.com/CodeMusic/daemons-companion/wiki/The-one-app), on the companion's wiki.)

New to the game itself? **[The player's manual](https://github.com/CodeMusic/DAEMONS/blob/main/docs/DAEMONS-manual.pdf)** (PDF) tells how to play it.

## Every page

| page | what it covers |
|---|---|
| [Running the playground](Running-the-playground) | `bindPlayground.sh`, its options, what it needs, and who it answers |
| [Editions and builds](Editions-and-builds) | CONTENT and CONTEXT, the DEBUG builds, the newest release or your own build |
| [Saves](Saves) | how the game's save is kept in the browser, a `.sav` to start from or download, a new game |
| [The COMPANION tab](The-COMPANION-tab) | a companion of the playground's own for each build, sending a daemon, from a phone, the site it shows |
| [WHAT'S NEW and HELP](WHATS-NEW-and-HELP) | each release's notes, the notice when a newer one lands, and the help page |
| [Playing on a phone](Playing-on-a-phone) | TAP TO PLAY, the keys and buttons, and where a tester's errors go |

## What is not here

**No ROM, and nothing of Nintendo's.** DAEMONS is built on pret's disassembly of a Nintendo game, so its ROMs are never
distributed. The playground reads them from a DAEMONS checkout on the machine that serves it, and answers only that
machine, a private network and the tailnet. It is for demos and beta tests among the people on your own network, never
a public site. To play DAEMONS on your own hardware, DAEMONS publishes **patches** for your own cartridge's game:
[Releases](https://github.com/CodeMusic/DAEMONS/wiki/Releases) on the DAEMONS wiki.

**No emulator either.** The game runs on [EmulatorJS](https://emulatorjs.org) (GPL-3.0) and its mGBA core, loaded from
EmulatorJS's own CDN, version 4.2.3.

## The DAEMONS family

| | |
|---|---|
| [CodeMusic/DAEMONS](https://github.com/CodeMusic/DAEMONS) ([wiki](https://github.com/CodeMusic/DAEMONS/wiki)) | **the game** -- its design, its tools, its releases and patches |
| [CodeMusic/pokefirered-daemons](https://github.com/CodeMusic/pokefirered-daemons) ([wiki](https://github.com/CodeMusic/pokefirered-daemons/wiki)) | the game's engine |
| [CodeMusic/daemons-companion](https://github.com/CodeMusic/daemons-companion) ([wiki](https://github.com/CodeMusic/daemons-companion/wiki)) | where a daemon goes when it leaves the game: the app, the hub, the boards |
| **CodeMusic/daemons-playground** | this: the game in a browser, with the companion beside it |
