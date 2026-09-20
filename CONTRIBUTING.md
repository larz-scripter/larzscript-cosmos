# Contributing

Physics corrections, new packages, better references and bug reports are all welcome.

## Setup

```sh
curl -fsSL https://raw.githubusercontent.com/larz-scripter/larzscript/main/install.sh | sh   # installs ~/.local/bin/larzscript
export PATH="$HOME/.local/bin:$PATH" LARZSCRIPT_PATH=packages
sh tests/run_tests.sh        # all suites (~30 s); pass a name to run one:  sh tests/run_tests.sh quantum
sh tests/run_examples.sh     # examples against their expected output
python3 tools/mutation_check.py quantum   # can the tests fail? (all packages: ~2.5 min)
```

## Adding or changing a function

1. Write it in the right `packages/<name>/main.lz` with a comment above it stating the formula and units - the comment becomes its line in `docs/API.md` (`python3 tools/gen_api.py`).
2. **Add a test that compares against something independent** - never a number you typed from memory or computed with the same code. Use a generator in `tools/` (see `gen_ref_physics.py`: 50-digit `decimal`, closed forms, or a separately written implementation), or a published value with its source in the test's label.
3. Test the edges: zero, tiny, huge, the limit where a formula loses digits (`1 - x`, `x - 1`, a difference of near-equal numbers), and every error path.
4. If you fix a numerical bug, first write the test that fails, and say in the commit what made the old code wrong.
5. Run `python3 tools/mutation_check.py <package>`; if you added something a wrong sign could silently break, add a mutant to that file.

## Rules of the house

- **Pure Larzscript, no dependencies.** Python is used only in `tools/` to generate references, and in `web/` to build the site.
- **No exponent literals** (see [docs/GOTCHAS.md](docs/GOTCHAS.md)) so the code runs on every existing Larzscript runtime, including the browser build. `physconst` is generated - edit `tools/gen_constants.py`, not the output.
- **Use `physmath.sqrt_`**, not the built-in `sqrt`, wherever the argument might be smaller than 1e-30 or larger than 1e30.
- **State your model's limits.** If a formula is only valid in some regime (weak field, non-relativistic, E < V0), say so in the comment and reject or handle inputs outside it.
- **Cite the source** of every constant and every non-obvious formula.
- Generated files (`tests/data_*.lz`, `packages/physconst`, `docs/API.md`) are checked by CI: regenerate them, do not hand-edit.

## The website

`web/` builds the larzos.com pages from this repository. See its header comments; `python3 web/sitegen/gen_site.py --help`. Every number quoted in the page text is computed by running the library, so changing a function updates the prose on the next build.
