# Changelog

## 0.1.0 - 2026-09-20

First release.

- `physmath`: trigonometry, exponentials, logarithms, inverse trig and hyperbolics, `log1p`, fractional powers, a correct `sqrt_` and `hypot`, number formatting. Verified to ~6e-16 against IEEE references.
- `physconst`: 41 constants generated from one reviewed table (SI 2019, CODATA 2018, IAU 2015).
- `complex`, `quantum` (state-vector simulator), `qalgo` (QFT, Grover, Deutsch-Jozsa, Bernstein-Vazirani, teleportation, phase estimation, CHSH, Shor), `qmech`, `relativity`, `astro`.
- 433 automated checks, 12 runnable examples, a 28-mutant mutation check, generated API reference.
- `web/`: builds the larzos.com/cosmos calculators; runs the library in a Web Worker on the Larzscript WebAssembly runtime.
