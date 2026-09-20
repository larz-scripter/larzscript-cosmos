# Larzscript gotchas

Things that shaped this code, found by running into them. Each was checked against the real interpreter (native 1.40-1.41 and the WebAssembly build).

**Numbers**
- **No exponent literals** (before [larzscript#18](https://github.com/larz-scripter/larzscript/pull/18) lands in a release): `6.626e-34` is not a number. `1.0e9` is `1.0` followed by an identifier `e9` - silently `1.0` inside a function. Write constants as plain decimals (`0.000...0006626`) or build them with `pow`. This repository's `physconst` is generated for exactly that reason.
- **`sqrt` is only reliable for about 1e-30 < x < 1e30** (fixed in [larzscript#17](https://github.com/larz-scripter/larzscript/pull/17)). Use `physmath.sqrt_`.
- **`pow` and `**` take only whole exponents.** `pow(2, 0.5)` is an error; use `physmath.powf`.
- **There is no `sin`, `cos`, `tan`, `exp`, `ln`, `atan2`** - see `physmath`.
- **`str(x)` prints six significant digits** (`str(123456789012.5)` is `1.23457e+11`). Use `physmath.fixed`, `sci` or `sig`.
- **`%` truncates toward zero**: `-7 % 4` is `-3`. Use `((a % n) + n) % n` for a true modulo.
- **`round` rounds halves away from zero** (`round(2.5)` is 3).
- **There are no bit operators** (`&`, `|`, `^`, `<<`). Use `//` and `%`.
- **`f"{x:.2f}"` ignores the format spec.**

**Syntax**
- **`for i from a to b` counts *down* when b < a**, so an empty range silently runs backwards. Use `for i in range(a, b)` whenever the range can be empty.
- **English operators are reserved words**, so they cannot be variable names: `at`, `is`, `more`, `less`, `than`, `least`, `most` (from `if x is at least 5`), plus `to`, `from`, `has`, `in`, `say`, `wait`, `unless` and the money words `price`, `pay`, `wallet`, `require`.
- **A string literal is limited to 8192 characters.** The website therefore writes each library file into the WebAssembly interpreter in chunks of 2000.
- **Defining a function with a builtin's name shadows the builtin** inside that module (`complex.abs`, `complex.sqrt`). Inside such a module, call the original through a differently named wrapper (`physmath.sqrt_`).

**Runtime**
- A module's top-level `let` is re-runnable: the interpreter in the browser keeps global scope between runs, so repeated `let x = ...` and `import ... as m` are fine and imports are cached.
- Errors are catchable: `try { ... } catch e { print(e["type"], e["message"]) }`; throw a dict with `type` and `message` for clean error text.
