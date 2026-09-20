#!/usr/bin/env python3
"""Independent reference for tests/test_quantum.lz.

Deliberately a DIFFERENT algorithm from packages/quantum: every gate is expanded into the
full 2^n x 2^n matrix (explicit Kronecker structure, big-endian: qubit 0 is the most
significant bit) and applied with a dense matrix-vector product. Slow, obvious, and shares
no code or indexing tricks with the in-place stride simulator it is checking.
Writes tests/data_quantum.lz."""
import cmath, math, random
from decimal import Decimal
random.seed(1234)
def lit(x):
    return "0" if x == 0 else format(Decimal(repr(float(x))), "f")

def bit(i, k, n): return (i >> (n - 1 - k)) & 1          # qubit k of basis index i

def single(n, k, U):
    d = 1 << n; M = [[0j] * d for _ in range(d)]
    for col in range(d):
        b = bit(col, k, n)
        for r in (0, 1):
            row = col & ~(1 << (n - 1 - k)) | (r << (n - 1 - k))
            M[row][col] += U[r][b]
    return M
def controlled(n, controls, k, U):
    d = 1 << n; M = [[0j] * d for _ in range(d)]
    for col in range(d):
        if all(bit(col, c, n) for c in controls):
            b = bit(col, k, n)
            for r in (0, 1):
                row = col & ~(1 << (n - 1 - k)) | (r << (n - 1 - k))
                M[row][col] += U[r][b]
        else:
            M[col][col] += 1
    return M
def cphase(n, a, b, phi):
    d = 1 << n; M = [[0j] * d for _ in range(d)]
    for i in range(d):
        M[i][i] = cmath.exp(1j * phi) if bit(i, a, n) and bit(i, b, n) else 1
    return M
def swapm(n, a, b):
    d = 1 << n; M = [[0j] * d for _ in range(d)]
    for col in range(d):
        ba, bb = bit(col, a, n), bit(col, b, n)
        row = col & ~(1 << (n - 1 - a)) & ~(1 << (n - 1 - b)) | (bb << (n - 1 - a)) | (ba << (n - 1 - b))
        M[row][col] = 1
    return M
s2 = 1 / math.sqrt(2)
H = [[s2, s2], [s2, -s2]]; X = [[0, 1], [1, 0]]; Y = [[0, -1j], [1j, 0]]; Zm = [[1, 0], [0, -1]]
def Ph(phi): return [[1, 0], [0, cmath.exp(1j * phi)]]
def RX(t): return [[math.cos(t/2), -1j*math.sin(t/2)], [-1j*math.sin(t/2), math.cos(t/2)]]
def RY(t): return [[math.cos(t/2), -math.sin(t/2)], [math.sin(t/2), math.cos(t/2)]]
def RZ(t): return [[cmath.exp(-1j*t/2), 0], [0, cmath.exp(1j*t/2)]]
FIXED = {"h": H, "x": X, "y": Y, "z": Zm, "s": Ph(math.pi/2), "sdg": Ph(-math.pi/2), "t": Ph(math.pi/4), "tdg": Ph(-math.pi/4)}
def matvec(M, v): return [sum(M[r][c] * v[c] for c in range(len(v))) for r in range(len(v))]
def op_matrix(n, op):
    name = op[0]
    if name in FIXED: return single(n, op[1], FIXED[name])
    if name == "rx": return single(n, op[1], RX(op[2]))
    if name == "ry": return single(n, op[1], RY(op[2]))
    if name == "rz": return single(n, op[1], RZ(op[2]))
    if name == "p":  return single(n, op[1], Ph(op[2]))
    if name == "cnot": return controlled(n, [op[1]], op[2], X)
    if name == "cz": return cphase(n, op[1], op[2], math.pi)
    if name == "cp": return cphase(n, op[1], op[2], op[3])
    if name == "swap": return swapm(n, op[1], op[2])
    if name == "ccx": return controlled(n, [op[1], op[2]], op[3], X)
    raise ValueError(name)
def run(n, ops):
    v = [0j] * (1 << n); v[0] = 1
    for op in ops: v = matvec(op_matrix(n, op), v)
    return v
def pauli_matrix(n, text):
    P = {"I": [[1, 0], [0, 1]], "X": X, "Y": Y, "Z": Zm}
    M = [[1]]
    for ch in text:   # explicit Kronecker product, qubit 0 leftmost
        A = P[ch]; M = [[M[i][j] * A[a][b] for j in range(len(M)) for b in range(2)] for i in range(len(M)) for a in range(2)]
    return M
def expect(n, v, text):
    M = pauli_matrix(n, text); w = matvec(M, v)
    return sum(v[i].conjugate() * w[i] for i in range(len(v))).real
def reduced_bloch_entropy(n, v, k):
    r00 = r11 = 0.0; r01 = 0j
    for i in range(1 << n):
        if bit(i, k, n) == 0:
            j = i | (1 << (n - 1 - k))
            r00 += abs(v[i]) ** 2; r11 += abs(v[j]) ** 2; r01 += v[i] * v[j].conjugate()
    # eigenvalues of [[r00, r01],[conj r01, r11]]
    tr, det = r00 + r11, r00 * r11 - abs(r01) ** 2
    disc = math.sqrt(max(tr * tr / 4 - det, 0)); l1, l2 = tr / 2 + disc, tr / 2 - disc
    ent = -sum(l * math.log2(l) for l in (l1, l2) if l > 1e-15)
    return [2 * r01.real, -2 * r01.imag, r00 - r11], ent

GATES1 = ["h", "x", "y", "z", "s", "sdg", "t", "tdg"]
def random_circuit(n, depth):
    ops = []
    for _ in range(depth):
        r = random.random()
        if r < 0.45: ops.append([random.choice(GATES1), random.randrange(n)])
        elif r < 0.65: ops.append([random.choice(["rx", "ry", "rz", "p"]), random.randrange(n), random.uniform(-6.3, 6.3)])
        elif r < 0.85 and n >= 2:
            a, b = random.sample(range(n), 2); ops.append([random.choice(["cnot", "cz", "swap"]), a, b])
        elif r < 0.93 and n >= 2:
            a, b = random.sample(range(n), 2); ops.append(["cp", a, b, random.uniform(-6.3, 6.3)])
        elif n >= 3:
            a, b, c = random.sample(range(n), 3); ops.append(["ccx", a, b, c])
    return ops
def op_lit(op): return "[" + ", ".join('"%s"' % o if isinstance(o, str) else (lit(o) if isinstance(o, float) else str(o)) for o in op) + "]"

cases = []
for n in (1, 2, 3, 3, 4, 4, 5, 5):
    for _ in range(6):
        ops = random_circuit(n, random.randint(4, 24)); v = run(n, ops)
        pauli = "".join(random.choice("IXYZ") for _ in range(n)) if n > 0 else "Z"
        k = random.randrange(n); bl, ent = reduced_bloch_entropy(n, v, k)
        cases.append((n, ops, v, pauli, expect(n, v, pauli), k, bl, ent))
with open("tests/data_quantum.lz", "w") as f:
    f.write("# GENERATED by tools/gen_ref_quantum.py (independent dense-matrix simulator) - do not edit.\n")
    f.write("# case: [n, circuit, [re...], [im...], pauli string, <pauli>, qubit k, bloch(k), entropy(k)]\nlet CASES = [\n")
    rows = []
    for n, ops, v, pauli, ex, k, bl, ent in cases:
        rows.append("  [%d, [%s], [%s], [%s], \"%s\", %s, %d, [%s], %s]" % (
            n, ", ".join(op_lit(o) for o in ops), ", ".join(lit(a.real) for a in v), ", ".join(lit(a.imag) for a in v),
            pauli, lit(ex), k, ", ".join(lit(b) for b in bl), lit(ent)))
    f.write(",\n".join(rows) + "\n]\n")
print("wrote tests/data_quantum.lz with", len(cases), "circuits")
