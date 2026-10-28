# Civilization III map corpus

Thousands of maps made by *Sid Meier's Civilization III: Complete*
(Conquests 1.22, by Firaxis Games, published by 2K) with its own random map
generator, for studying how that generator works. [OpenCiv3](https://github.com/C7-Game/Prototype)'s
map generator is checked against these maps, seed by seed.

Each map is the unmodified game's 4000 BC autosave (`.SAV`) of a new game,
made by driving the game with the scripts in [`scripts/`](scripts): a New
Game from a seed, or a Quick Start from a random one. The saves hold no game
art, sound or text beyond what any Civ3 save holds.

## Layout

```
<machine>/<source>/<YYYY-MM-DD_HH00>/
    maps.zip       the saves made that hour (maps_1.zip, maps_2.zip... if many)
    manifest.csv   name, rules, size, bytes, sha1 of each save
    seeds.csv      name, seed, landform, water, climate, temperature, age, civs
```

`<machine>` is the PC that made them, `<source>` is `host` (the game run on
that PC) or `vm_civ3gen-<n>` (one of its VMs). A batch is pushed every hour.

## File names

`STD_Standard_Pan70_Nrm-Tmp-4B_s1239439989.SAV` is a map made with the
standard rules, at Standard size (100x100, 8 civs), Pangaea at 70% water,
normal climate, temperate, 4 billion years, from world seed 1239439989. A
seed with its settings makes the same map in Civ3 every time.

| part | values |
|---|---|
| landform | `Pan` Pangaea, `Con` Continents, `Arc` Archipelago |
| water | `80`, `70`, `60` (% of the world) |
| climate | `Ari` arid, `Nrm` normal, `Wet` wet |
| temperature | `Wrm` warm, `Tmp` temperate, `Col` cool |
| age | `3B`, `4B`, `5B` billion years |

Quick Start maps are first saved as `..._t<time>.SAV`; their seed is only in
the save, and they are renamed to `_s<seed>` once their settings are checked
against the name. In a save's WRLD section: `WorldSeed`, `ActualLandform`
(0 Archipelago, 1 Continents, 2 Pangaea), `ActualOceanCoverage` (0 = 80%,
1 = 70%, 2 = 60%), `ActualClimate` (0 arid, 1 normal, 2 wet),
`ActualTemperature` (0 cool, 1 temperate, 2 warm), `ActualAge` (0 = 3, 1 = 4, 2 = 5
billion years).

Civilization III is a trademark of Take-Two Interactive Software, Inc. This
corpus is not affiliated with or endorsed by Firaxis, 2K or Take-Two.
