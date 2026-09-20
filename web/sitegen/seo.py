"""Final SEO titles and meta descriptions. Search engines show roughly 60 characters of a title and
155-160 of a description; longer text is cut mid-word. gen_site.py refuses to build if these overflow."""
SEO = {
 "quantum-circuit-simulator": ("Quantum Circuit Simulator — Online, Up to 10 Qubits, Free",
    "Free online quantum circuit simulator: build circuits with H, CNOT, T and rotations, then see exact probabilities, measurements, the state vector and entanglement."),
 "grover-search-simulator": ("Grover's Algorithm Simulator — Quantum Search Step by Step",
    "Free Grover's algorithm simulator: run quantum search on up to 1,024 items and see the exact success probability, the optimal iterations and the overshoot curve."),
 "shor-algorithm-simulator": ("Shor's Algorithm Simulator — Factor 15 and 21 on Qubits",
    "Free Shor's algorithm simulator: watch a simulated quantum computer factor 15 and 21 by finding the period of aˣ mod N, with a real quantum Fourier transform."),
 "quantum-teleportation-simulator": ("Quantum Teleportation Simulator — Bloch Sphere & Fidelity",
    "Free quantum teleportation simulator: teleport any qubit state and check that all four measurement outcomes give fidelity 1, with the Bell pair and corrections."),
 "bell-inequality-calculator": ("Bell Inequality Calculator — CHSH Value & Entanglement",
    "Free Bell inequality calculator: choose four detector angles, simulate an entangled pair and get the CHSH value S against the classical limit 2 and 2√2."),
 "hydrogen-spectrum-calculator": ("Hydrogen Spectrum Calculator — Balmer, Lyman & Paschen Lines",
    "Free hydrogen spectrum calculator: wavelength, energy and colour of any Bohr-model transition — Balmer, Lyman, Paschen series. Verified against CODATA."),
 "de-broglie-wavelength-calculator": ("de Broglie Wavelength Calculator — Electrons, Neutrons & More",
    "Free de Broglie wavelength calculator with relativistic momentum: electrons at any voltage (electron microscopes), neutrons, protons and even a baseball."),
 "particle-in-a-box-calculator": ("Particle in a Box Calculator — Energy Levels & Probability",
    "Free particle-in-a-box calculator: energy levels, photon wavelengths, probability-density plot and exact region probabilities for an electron, proton or any mass."),
 "quantum-tunneling-calculator": ("Quantum Tunneling Calculator — Barrier Transmission",
    "Free quantum tunneling calculator: the exact transmission probability of an electron, proton or neutron through a rectangular barrier, with a width curve."),
 "time-dilation-calculator": ("Time Dilation Calculator — Lorentz Factor & Length",
    "Free time dilation calculator: enter a speed to get the Lorentz factor, dilated time, length contraction and kinetic energy, computed by verified open-source code."),
 "black-hole-calculator": ("Black Hole Calculator — Radius, Hawking Temperature, Lifetime",
    "Free black hole calculator: enter a mass to get the Schwarzschild radius, photon sphere, Hawking temperature, evaporation time and entropy from verified physics."),
 "relativistic-rocket-calculator": ("Relativistic Rocket Calculator — Ship Time at 1 g",
    "Free relativistic rocket calculator: how long does a 1 g trip to Alpha Centauri or Andromeda take on the ship and on Earth? Exact special relativity, live."),
 "universe-age-calculator": ("Age of the Universe Calculator — Hubble Constant & Distances",
    "Free age of the universe calculator: enter the Hubble constant and matter density to get the age, look-back time and comoving, luminosity and angular distances."),
 "cosmos": ("Larzscript Cosmos — Quantum, Relativity & Space Calculators",
    "Free, verified physics calculators running open-source Larzscript in your browser: quantum circuits, Grover, Shor, hydrogen, black holes, time dilation and more."),
}
def check():
    for slug, (t, d) in SEO.items():
        assert len(t) <= 62, (slug, "title", len(t), t)
        assert 110 <= len(d) <= 165, (slug, "description", len(d), d)
if __name__ == "__main__":
    check(); print("all", len(SEO), "SEO strings within limits:", {s: (len(t), len(d)) for s, (t, d) in SEO.items()})
