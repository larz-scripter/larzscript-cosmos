# larzscript-cosmos

**Quantum computing, quantum mechanics, relativity and astrophysics - written entirely in [Larzscript](https://github.com/larz-scripter/larzscript). Zero dependencies, 454 automated checks, and every calculator runs live in your browser.**

[![test](https://github.com/larz-scripter/larzscript-cosmos/actions/workflows/test.yml/badge.svg)](https://github.com/larz-scripter/larzscript-cosmos/actions/workflows/test.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Try it now, no install: **[larzos.com/cosmos/](https://larzos.com/cosmos/)** - the same code that is in this repository, compiled to WebAssembly and running in your browser tab.

| Quantum computing | Quantum mechanics | Relativity & cosmology |
|---|---|---|
| [Circuit simulator](https://larzos.com/quantum-circuit-simulator/) (up to 10 qubits) | [Hydrogen spectrum](https://larzos.com/hydrogen-spectrum-calculator/) | [Time dilation](https://larzos.com/time-dilation-calculator/) |
| [Grover search](https://larzos.com/grover-search-simulator/) | [de Broglie wavelength](https://larzos.com/de-broglie-wavelength-calculator/) | [Black holes](https://larzos.com/black-hole-calculator/) |
| [Shor's algorithm](https://larzos.com/shor-algorithm-simulator/) (factors 15 and 21) | [Particle in a box](https://larzos.com/particle-in-a-box-calculator/) | [Relativistic rocket](https://larzos.com/relativistic-rocket-calculator/) |
| [Teleportation](https://larzos.com/quantum-teleportation-simulator/) | [Quantum tunneling](https://larzos.com/quantum-tunneling-calculator/) | [Age of the universe](https://larzos.com/universe-age-calculator/) |
| [Bell inequality (CHSH)](https://larzos.com/bell-inequality-calculator/) | | |

## A taste

```
import "quantum" as q

let s = q.zero(2)            # two qubits, both |0>
q.h(s, 0)                    # Hadamard on qubit 0
q.cnot(s, 0, 1)              # entangle qubit 1 with it

print(q.state_str(s, 4))     # 0.7071|00> + 0.7071|11>
print(q.entropy(s, 0))       # 1  (one full bit of entanglement)
print(q.sample(s, 1000))     # {00: 467, 11: 533}   (seeded, reproducible)
```

Shor's algorithm, on a simulated 12-qubit quantum computer:

```
$ larzscript examples/03_shor_factor_15.lz
a = 2: period 4  factors [3, 5]
a = 7: period 4  factors [3, 5]
a = 14: nil   (14 = -1 mod 15: a known failure case)
```

The hydrogen atom, from the Bohr model with the proton's finite mass, in vacuum and in air:

```
$ larzscript examples/05_hydrogen_balmer.lz
n=3 -> 2   vacuum 656.470 nm   air 656.288 nm   1.8887 eV
n=4 -> 2   vacuum 486.274 nm   air 486.138 nm   2.5497 eV
```

GPS satellites, where two effects of relativity fight each other:

```
$ larzscript examples/09_gps_clock.lz
gravity (weaker up there): +45.65 microseconds/day
orbital speed:             -7.21 microseconds/day
net:                       +38.44 microseconds/day
uncorrected, positions would drift by 11.5 km per day
```

Twelve runnable examples with checked outputs live in [`examples/`](examples/).

## What is inside

| Package | What it gives you |
|---|---|
| [`physmath`](packages/physmath/main.lz) | The maths Larzscript does not ship: `sin` `cos` `tan` `exp` `ln` `atan2` `asin` `sinh` `asinh` `log1p` fractional powers, a **correct** `sqrt`, and number formatting (`fixed`, `sci`, `sig`). Accurate to ~5e-16. |
| [`physconst`](packages/physconst/main.lz) | 41 constants - SI 2019 exact, CODATA 2018, IAU 2015 - each with its unit, kind, source and uncertainty. Generated from one reviewed table. |
| [`complex`](packages/complex/main.lz) | Complex numbers. |
| [`quantum`](packages/quantum/main.lz) | State-vector quantum-circuit simulator: H X Y Z S T, rotations, CNOT, CZ, controlled phase, SWAP, Toffoli, measurement, sampling, Bloch vectors, entanglement entropy, Pauli expectations, a circuit text format and ASCII circuit diagrams. ~30 ms per gate at 12 qubits. |
| [`qalgo`](packages/qalgo/main.lz) | Quantum Fourier transform, Grover, Deutsch-Jozsa, Bernstein-Vazirani, teleportation, phase estimation, the CHSH Bell test, and **Shor's algorithm**. |
| [`qmech`](packages/qmech/main.lz) | Hydrogen levels and spectral series, photons, de Broglie waves (relativistic), Heisenberg, particle in a box, harmonic oscillator, rectangular-barrier tunneling. |
| [`relativity`](packages/relativity/main.lz) | Lorentz factor, time dilation, length contraction, velocity addition, Doppler, E = gamma mc^2, the relativistic rocket, Schwarzschild black holes, Hawking radiation, Bekenstein-Hawking entropy, GPS. |
| [`astro`](packages/astro/main.lz) | Stefan-Boltzmann, Wien, magnitudes, equilibrium temperature, transits, Kepler's third law, flat-LCDM ages and distances. |

The full function list is in [`docs/API.md`](docs/API.md), generated from the source.

## Install and run

You need a `larzscript` binary ([latest release](https://github.com/larz-scripter/larzscript/releases/latest), one file, no dependencies):

```sh
curl -fsSL https://raw.githubusercontent.com/larz-scripter/larzscript/main/install.sh | sh
git clone https://github.com/larz-scripter/larzscript-cosmos && cd larzscript-cosmos
export LARZSCRIPT_PATH=packages          # so `import "quantum"` finds the packages
larzscript examples/01_bell_state.lz
sh tests/run_tests.sh                    # 454 checks, about half a minute
sh tests/run_examples.sh                 # 12 examples against their expected output
```

## How do you know the numbers are right?

Larzscript has no `sin`, `cos`, `exp` or `ln`, its `str()` prints six digits, and (until [larzscript#17](https://github.com/larz-scripter/larzscript/pull/17)) its built-in `sqrt` is wrong below about 10^-36. So this project starts by writing and *testing* a numerical core, then verifies everything above it against something independent:

- **IEEE references.** `physmath` is compared with Python's `math` at hundreds of points per function across the whole double range: worst relative error 5e-16 (about two units in the last place).
- **A second implementation.** The quantum simulator is checked against a deliberately different one that builds every gate as a full 2^n x 2^n matrix. 48 random circuits, plus Pauli expectations, Bloch vectors and entropies, agree to 1e-12.
- **High precision.** Relativity is compared with 50-digit decimal arithmetic; that is what caught two cancellation bugs (the rocket and gravitational redshift) that ordinary float references would have shared.
- **Closed forms.** The quantum Fourier transform against the DFT; Grover against sin^2((2k+1)theta); universe ages against the exact `asinh` solution; matter-only cosmology against 2c/H0 (1 - 1/sqrt(1+z)).
- **Published values.** GPS +38 microseconds/day, the Sun's 2.95 km Schwarzschild radius, Hawking T = 6.17e-8 K, hydrogen's Balmer lines, 100 kV electrons at 3.70 pm, the Planck-2018 age 13.80 Gyr.
- **The tests can fail.** [`tools/mutation_check.py`](tools/mutation_check.py) breaks the code in 33 ways (a flipped sign, swapped control and target, a wrong constant...) and requires the suite to notice every time.

See [`docs/VERIFICATION.md`](docs/VERIFICATION.md) for the method, the bugs it found (including two in Larzscript itself), and what is *not* verified.

## Known limits

Ideal noiseless qubits; the Bohr model (no fine structure); non-rotating black holes; flat LCDM without radiation; special relativity in flat space. Each calculator page states its own limits. Larzscript quirks that shaped the code are in [`docs/GOTCHAS.md`](docs/GOTCHAS.md).

## The website

[`web/`](web/) builds the [larzos.com/cosmos/](https://larzos.com/cosmos/) pages: it bundles these exact package files, runs them in a Web Worker on the Larzscript WebAssembly runtime, and writes every number quoted in the page text by *running the library at build time*, so the prose cannot disagree with the tool.

## Contributing

Ideas, bug reports, physics corrections and new packages are welcome - see [CONTRIBUTING.md](CONTRIBUTING.md) and the [roadmap](ROADMAP.md). Cite as in [CITATION.cff](CITATION.cff). MIT licensed.
