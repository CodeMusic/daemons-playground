# Playing on a phone

Open the tailnet address `./bindPlayground.sh` prints. The buttons are on the screen, laid out as on a GBA.

## TAP TO PLAY

An iPhone (Safari and Chrome alike) starts a page's sound only inside a tap. The game starts a few seconds after the
tap on PLAY, once the emulator and the ROM have arrived, so its sound waits -- and the emulator waits on its sound, and
the screen stays blank. The page puts **TAP TO PLAY** over the game, and that tap starts it. It comes back if the phone
interrupts the sound later (a call, the lock screen). On a computer the sound runs from the PLAY press, and it never
shows.

## Keys, on a computer

| | |
|---|---|
| arrows | move |
| **X** | A |
| **Z** | B |
| **Enter** | START |
| **V** | SELECT |
| **Q**, **E** | L, R |

X and Z are as in mGBA (EmulatorJS's own default is the other way round). Change them with the controller button under
the game; a mapping you chose is kept.

## When something goes wrong on a tester's device

A phone has no console to read, so the page tells **the playground's own output** -- in the terminal where
`./bindPlayground.sh` runs -- its errors, what EmulatorJS warns of, and a line as each game starts (`N frames in 5 s, sound running`).
