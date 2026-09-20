# Roadmap

Ideas, roughly in order. Open an issue to argue for a different order or to claim one.

**Physics**
- Density-matrix simulation and simple noise channels (bit flip, dephasing, depolarising) - so circuits can be run "on imperfect hardware".
- More algorithms: VQE on a small Hamiltonian, quantum counting, amplitude estimation, the quantum walk.
- Hydrogen with fine structure and the Lamb shift; hydrogen-like ions; helium's lowest levels.
- Kerr (spinning) black holes: horizon, ergosphere, ISCO as a function of spin.
- Orbits: bring `larzscript-packages/orbits` (Kepler, Hohmann) in as a dependency instead of re-deriving.
- CODATA 2022 constants.

**Library**
- Register the packages in the Larzscript package registry so `larzscript pkg install quantum` works.
- A `units` integration so calculators can take and return quantities with units.
- Larger simulations: a packed-amplitude representation (one list) and a benchmark suite.

**Website**
- A Bloch-sphere visualisation for the teleportation and circuit pages.
- Shareable links (inputs encoded in the URL).
- Explanation pages: what is a qubit, entanglement without the mysticism, why Shor needs a quantum computer.
