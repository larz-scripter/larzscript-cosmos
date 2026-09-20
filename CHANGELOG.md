# Changelog

## 0.1.1 - 2026-09-20

**Bug fix - please upgrade if you used `qalgo.shor` or the circuit-simulator page.**

- `qalgo.shor` (and the Shor page) reported its "strongest peaks" in index order (y = 255, 254, ...) with probability 0, because the built-in `sorted()` silently leaves a list of pairs unsorted. The period it printed was still correct, but it was found by trying every multiple of 1 (a classical brute-force search), not read off the measurement peaks, so the page's claim was not true for 0.1.0. Now: outcomes are ranked by probability, denominator 1 is rejected, the period comes from the continued-fraction denominator of a genuine peak (`peak_y`, `peak_denominator` are returned), and tests assert the peaks are sorted and sit at y = 64, 128, 192 for N = 15, a = 7.
- The circuit-simulator page had the same ordering bug in its "most probable states" and "measurement counts" tables.
- New `physmath.sort_by(items, key, descending=false)`: stable merge sort for any list.
- Tests now cover peak provenance; 33-mutant mutation check (was 28).

## 0.1.0 - 2026-09-20

First release.

- `physmath`: trigonometry, exponentials, logarithms, inverse trig and hyperbolics, `log1p`, fractional powers, a correct `sqrt_` and `hypot`, number formatting. Verified to ~6e-16 against IEEE references.
- `physconst`: 41 constants generated from one reviewed table (SI 2019, CODATA 2018, IAU 2015).
- `complex`, `quantum` (state-vector simulator), `qalgo` (QFT, Grover, Deutsch-Jozsa, Bernstein-Vazirani, teleportation, phase estimation, CHSH, Shor), `qmech`, `relativity`, `astro`.
- 454 automated checks, 12 runnable examples, a 33-mutant mutation check, generated API reference.
- `web/`: builds the larzos.com/cosmos calculators; runs the library in a Web Worker on the Larzscript WebAssembly runtime.
