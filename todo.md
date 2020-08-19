### Features to implement:
- Add hard AI (through deep reinforcement?)
- Add way to view all options during party selection
- Add long descriptions for special effects/statuses?

### Other fixes:
- check ```# TODO``` tags in code
- Passives give double instances of resistances character has natively
  - Should this be removed? Just in display?
- Make sure that "Health full" message is printed when at full health and hit by Dia/Diarama
  - Also: consider rearranging healing to its own effect instead of incorporating in damage formula

### Things to check with game:
- Do bind or stun affect crit rate? If so, by how much?
- Check if lakshmi has an "h"
- Crit rate of Divine Shot is definitely off: listed as 30 but putting in 55
  - Probably off for other moves?
- Anti-Expel/Death are weird and probably not implemented right
  - https://gamefaqs.gamespot.com/ps2/582958-shin-megami-tensei-nocturne/faqs/35024
  - Stack with innate resistance
  - Don't affect direct damage (test this)
  - How do they affect thunderclap?
- Focus doesn't work with multihits?
  - Check exactly how this works in-game (Deathbound? Andalucia?)
- Does Dekaja effect of Hell Exhaust trigger on dodge? void?
- Setting Ice Breath to 5 hits instead of 4 to match Fire Breath/Shock/Wing Buffet— verify this
- Right now, Endure triggers when using moves like Sacrifice— should it?
- Check how voids/absorbs work if target is stoned
- Does Guillotine inflict stun?
- Check if God's Bow misses
- Check if Last Resort misses
- Test if Pestilence can miss (listed accuracy is 255)
- Missing info on correction/limits of Kamikaze/Last Resort/Sacrifice
  - Also check if Sacrifice is 4-hit or 5-hit
  - Right now, guessing missing values— I guess check to see if they're somewhat consistent with the game
- Verify that Evil Gaze missed (as in dodge) instead of proccing
  - Also check print msg
- Does Recarmdra revive? Or just heal?
- Dia and Diarama formulas are unknown
  — Right now, using Agilao/Agidyne numbers
- Does Drain Attack trigger on counter?
- Do sleeping demons wake up on any kind of hit?
- Double-check life stone/chakra drop heal percentage
- Can 200 accuracy moves miss? (Earthquake, Yoshitsune)
- Does freeze chance increase on ice-weak enemies?
- Does freezing stop Fire Repel on Surt's attack?
  - Check category or element when redefining effectiveness?
- Check if Tetrakarn reflects all parts of multihit moves
- Check what message displays on 5th Debilitate or 3rd Taunt
- Check Tekisatsu (Stinger) crit rate? felt like higher than 4

