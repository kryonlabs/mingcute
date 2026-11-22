# mingcute

The MingCute Core icon set (Apache-2.0) as a Ziran package: about 3,300 icons
in the filled and regular styles plus a few matching `extra` icons. Each icon
is one module holding one constant, `Shape`, so importing an icon carries only
that icon. README.md documents module naming and usage.

## Layout

| Path | Contents |
| --- | --- |
| `svg/` | Source SVG files, per style (`filled`, `regular`) |
| `src/` | Generated Ziran modules, flat so Ziran resolves them |
| `scripts/generate.py` | Turns `svg/` into `src/` and the module list in `ziran.toml` |
| `SKIPPED.txt` | Icons built on gradients or dashes that are not generated |

## Commands

After updating `svg/`, regenerate with `scripts/generate.py` and the MingCute
revision; commit the regenerated `src/` and `ziran.toml` together.

## Dependencies

No runtime dependencies. Icons feed Kryon's icon widget through `Shape`.
