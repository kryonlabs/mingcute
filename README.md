# mingcute

The [MingCute](https://github.com/mingcute-design/mingcute-icons) Core icon
set (Apache-2.0) as a Ziran package: about 3,300 icons in the filled and
regular styles, plus a few drawn to match (`extra`, such as spreadsheet row and
column insert and remove).

Each icon is its own module holding one constant, `Shape`, so an application
that imports an icon carries only that icon:

```zi
Table :: #import "mingcute_regular_table";
// Table.Shape is the icon's drawing operations, ready for Kryon's icon widget.
```

Module names are `mingcute_<style>_<name>`, where style is `filled`, `regular`
or `extra` and name is MingCute's file name (`table`, `save_2`, `delete_2`).
Find a name with `ls svg/regular/*`; the modules are flat under `src/`, which is where Ziran looks.

`svg/` holds the source files. `scripts/generate.py` turns them into `src/` and
`ziran.toml`; run it with the MingCute revision after updating `svg/`. Icons
built on gradients or dashes are skipped and listed in `SKIPPED.txt`.
