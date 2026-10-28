# Editions and builds

The start page offers DAEMONS' two editions:

| | |
|---|---|
| **CONTENT** | DAEMONS on FireRed's engine |
| **CONTEXT** | DAEMONS on LeafGreen's engine |

The two editions' differences, and why there are two: [Editions](https://github.com/CodeMusic/DAEMONS/wiki/Editions)
on the DAEMONS wiki.

**DEBUG** plays the testing build of either edition: a game that starts as a normal one does, with DAEMONS' DEBUG menu
to reach things without playing to them. It is for testing, not for a first play.

## Which release

**The newest release, always.** The ROMs are read from DAEMONS' `ROM RELEASE/` each time a game starts, so a release
made while the playground runs is played by the next game. If a newer release lands while you play, the page says so
([WHAT'S NEW and HELP](WHATS-NEW-and-HELP)).

`./bindPlayground.sh --build` plays DAEMONS' own `engineGba` build instead, to try a change before it is released.

Each build keeps its own save and its own companion: CONTENT, CONTEXT and their two DEBUG builds never share one
([Saves](Saves), [The COMPANION tab](The-COMPANION-tab)).
