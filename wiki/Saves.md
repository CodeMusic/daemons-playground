# Saves

## Starting

Start a **new game**, or continue from a **`.sav`** you choose: from mGBA, Delta, or a cart. mGBA's 131,088-byte files
(its clock after the flash) load as they are; a saved game is 128 KB.

With no `.sav` chosen, the save the page kept for that build last time is offered -- continue it, download it, or start
a new game. It is never silently continued, and never silently lost.

## How it is kept

EmulatorJS keeps a game's save in the browser while it runs, but lets it go when the page is left. So the page keeps
its own copy: it checks the game's save every five seconds and whenever the page is hidden or closed, and stores it in
the browser's IndexedDB under the build's name whenever it has changed.

**Download save**, under the game, gives you the save as a `.sav` at any moment, for mGBA, Delta or a cart.

The page also posts the save to the playground whenever it changes (`data/saves/`), which is how
[the COMPANION tab](The-COMPANION-tab) reads it.

## A new game

A new game puts the old save aside as `data/saves/*.before-new-game.sav` on the playground's machine. If the build's
companion is already married to another game, it says so and offers to start fresh; the old one is kept aside as
`data/companions/<build>.before`.

## One save per build, for everyone

Two people playing the same build on one playground at once share its save and its companion, and each one's save
replaces the other's. For a beta test with several people at once, give each a different build, or a playground of
their own.
