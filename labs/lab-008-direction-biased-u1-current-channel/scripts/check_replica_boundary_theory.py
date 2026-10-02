"""Independent finite checks of replica identities and analytic long-path rate.

No decoder output or fitted critical point enters these checks.
"""
from itertools import product
from math import comb
from pathlib import Path
import hashlib
import json
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import gammaln, logsumexp
from scipy.integrate import quad
from current_oracle import LAB, ROOT, square_graph, charge_matrix, exact_enumeration


def K(phi, p, q):
    return 1-p+p*q*np.exp(1j*phi)+p*(1-q)*np.exp(-1j*phi)


def replica_integral(D, cut, R, marked, p, q):
    n = 9
    M = D.shape[0]
    independent = np.indices((n,)*((R-1)*M)).reshape((R-1)*M, -1).T
    independent = independent.reshape(-1, R-1, M)*(2*np.pi/n)
    theta = np.concatenate([independent, -independent.sum(axis=1, keepdims=True)], axis=1)
    phi = theta @ D
    twists = np.array([a < marked for a in range(R)])[None, :, None]*np.pi*cut
    return np.prod(K(phi+twists, p, q), axis=(1, 2)).mean()


def path_sectors(d, p, q):
    table = {}
    for values in product((0, 1, -1), repeat=d):
        j = np.array(values)
        w = np.prod(np.where(j == 0, 1-p, np.where(j == 1, p*q, p*(1-q))))
        Q = tuple(j[:-1]-j[1:])
        table.setdefault(Q, np.zeros(2))[abs(int(j[-1])) % 2] += w
    return np.array(list(table.values()))


def path_log_risk(d, p, q):
    if q == 1:
        return d*np.log(p)
    k = np.arange(d+1)
    logbinom = gammaln(d+1)-gammaln(k+1)-gammaln(d-k+1)
    left = (d-k)*np.log1p(-p)+k*np.log(p*q)
    right = k*np.log1p(-p)+(d-k)*np.log(p*(1-q))
    return float(logsumexp(logbinom+np.minimum(left, right)))


def path_rate(p, q):
    if q == 1:
        return -np.log(p), None
    a, b, c = 1-p, p*q, p*(1-q)
    def log_overlap(s):
        return np.logaddexp(s*np.log(a)+(1-s)*np.log(c),
                            s*np.log(b)+(1-s)*np.log(a))
    res = minimize_scalar(log_overlap, bounds=(0, 1), method='bounded',
                          options={'xatol': 1e-14})
    s = min((0., 1., float(res.x)), key=log_overlap)
    return -float(log_overlap(s)), s


def square_genie_bound(L, p, q):
    path_risk = np.exp(path_log_risk(L-1, p, q))
    return float(-np.expm1(L*np.log1p(-2*path_risk))/2)


def moment_result(z):
    A0, A1 = z.sum(axis=1), z[:, 0]-z[:, 1]
    keep = A0 > 0
    A0, A1 = A0[keep], A1[keep]
    assert abs(A0.sum()-1) < 1e-12
    m = A1/A0
    risk = float(np.minimum(z[:, 0], z[:, 1]).sum())
    M2 = float(np.sum(A0*m*m))
    lo, hi = (1-M2)/4, (1-M2)/2
    assert lo-1e-12 <= risk <= hi+1e-12
    series = []
    y = np.maximum(0, 1-m*m)
    for N in (1, 2, 4, 8):
        partial = sum(comb(2*k, k)/(4**k*(2*k-1))*np.sum(A0*y**k)/2
                      for k in range(1, N+1))
        tail = comb(2*N, N)/4**N*np.sum(A0*y**(N+1))/2
        assert partial-1e-12 <= risk <= partial+tail+1e-12
        series.append({'N': N, 'lower': float(partial), 'upper': float(partial+tail)})
    # Finite-graph continuation is well-defined independently of the integers.
    def cont(R):
        weights = A0**R
        return float(np.sum(weights*m*m)/weights.sum())
    assert abs(cont(1)-M2) < 1e-12
    return {'LER': risk, 'M2': M2, 'LER_lower': lo, 'LER_upper': hi,
            'annealed_R2_ratio': cont(2), 'moment_series': series,
            'M_even_0_to_8': [float(np.sum(A0*m**(2*k))) for k in range(5)]}


def gaussian_annulus_check(A):
    """Conditional continuum ansatz; independent lattice sum vs kernel integral."""
    cutoff = int(np.ceil((np.pi+np.sqrt(180*A))/(2*np.pi)))+1
    images = np.arange(-cutoff, cutoff+1)
    signs = np.where(images % 2 == 0, 1., -1.)
    def kernels(x):
        terms = np.sqrt(np.pi/A)*np.exp(-(x-2*np.pi*images)**2/(4*A))
        return terms.sum(), terms @ signs
    def integral(R, marked):
        def integrand(x):
            f, g = kernels(x)
            return g**marked*f**(R-marked)
        return quad(integrand, -np.pi, np.pi, epsabs=1e-12, epsrel=1e-12)[0]/(2*np.pi)
    errors = []
    nmax = int(np.ceil(np.sqrt(45/A)))+1
    for R in (2, 3, 4):
        n = np.array(list(product(range(-nmax, nmax+1), repeat=R-1)))
        for marked in (0, 2):
            last = -marked//2-n.sum(axis=1)
            winding = np.column_stack([n, last]).astype(float)
            winding[:, :marked] += .5
            value = np.exp(-A*np.sum(winding*winding, axis=1)).sum()
            errors.append(abs(value-integral(R, marked)))
    assert max(errors) < 1e-10
    M2 = integral(1, 2)
    risk = .5*(1-quad(lambda x: abs(kernels(x)[1]), -np.pi, np.pi,
                     epsabs=1e-12, epsrel=1e-12)[0]/(2*np.pi))
    n = np.arange(nmax+1)
    series_risk = .5-2/np.pi*np.sum((-1.)**n/(2*n+1)*np.exp(-A*(n+.5)**2))
    assert abs(risk-series_risk) < 1e-12
    assert (1-M2)/4-1e-12 <= risk <= (1-M2)/2+1e-12
    return {'A': float(A), 'M2': M2, 'LER_ansatz': float(risk),
            'LER_series': float(series_risk), 'integer_R_root_sum_max_error': float(max(errors)),
            'interpretation': 'Conditional Gaussian annulus with prescribed replica continuation; not physical square critical LER.'}


def main():
    grid = [(p, q) for p in (.1, .3, .46) for q in (.5, .75, .97, 1.)]
    g = square_graph(3)
    D = charge_matrix(g)
    cut = np.array([e in g.logical_edges for e in range(len(g.edges))])
    square, paths, kernels = [], [], []
    quad_max = 0.
    for p, q in grid:
        angles = np.arange(9)*2*np.pi/9
        T = K(angles[None, :]-angles[:, None], p, q)/9
        hermitian = np.max(np.abs(T-T.conj().T))
        eig_error = np.max(np.abs(np.linalg.eigvalsh(T)-np.sort([0.]*6+[1-p, p*q, p*(1-q)])))
        phi = np.linspace(-np.pi, np.pi, 257)
        G = (1-p)**2+p*p*(q*q+(1-q)**2)+2*p*(1-p)*np.cos(phi)+2*p*p*q*(1-q)*np.cos(2*phi)
        harmonic_error = np.max(np.abs(G-np.abs(K(phi, p, q))**2))
        assert max(hermitian, eig_error, harmonic_error) < 1e-12
        kernels.append({'p': p, 'q': q, 'Hermitian_error': float(hermitian),
                        'spectrum_error': float(eig_error), 'R2_harmonic_error': float(harmonic_error)})
        table = exact_enumeration(g, p, q)
        z = np.array([v[0] for v in table.values()])
        moments = moment_result(z)
        genie_bound = square_genie_bound(3, p, q)
        assert genie_bound <= moments['LER']+1e-12
        A0, A1 = z.sum(axis=1), z[:, 0]-z[:, 1]
        errors = []
        for marked, expected in ((0, np.sum(A0**2)), (2, np.sum(A1**2))):
            actual = replica_integral(D, cut, 2, marked, p, q)
            errors.append(float(abs(actual-expected)))
        path_z = path_sectors(2, p, q)
        path_A0, path_A1 = path_z.sum(axis=1), path_z[:, 0]-path_z[:, 1]
        for marked, expected in ((0, np.sum(path_A0**3)), (2, np.sum(path_A1**2*path_A0))):
            actual = replica_integral(np.array([[1, -1]]), np.array([0, 1]), 3, marked, p, q)
            errors.append(float(abs(actual-expected)))
        quad_max = max(quad_max, *errors)
        assert max(errors) < 1e-12
        square.append({'L': 3, 'p': p, 'q': q, 'records': len(table),
                       **moments, 'vertical_current_genie_lower_bound': genie_bound,
                       'replica_integral_errors_R2_square_R3_path': errors})
        tau, s = path_rate(p, q)
        rates = []
        for d in (32, 128, 512, 2048):
            finite = -path_log_risk(d, p, q)/d
            assert finite >= tau-1e-12
            rates.append({'d': d, 'minus_log_LER_per_edge': finite, 'gap_to_limit': finite-tau})
        assert abs(rates[-1]['gap_to_limit']) < .01
        if q == .5:
            assert abs(tau+np.log(2*p*(1-p))/2) < 1e-12
        paths.append({'p': p, 'q': q, 'tau': tau, 'Chernoff_s': s, 'finite_rates': rates})
    x = np.linspace(0, 1, 1001)
    series_checks = []
    for N in (1, 2, 4, 8):
        partial = sum(comb(2*k, k)/(4**k*(2*k-1))*(1-x*x)**k/2 for k in range(1, N+1))
        true = (1-x)/2
        uniform_tail = comb(2*N, N)/4**N/2
        upper = partial+uniform_tail*(1-x*x)**(N+1)
        assert np.min(true-partial) >= -1e-12 and np.min(upper-true) >= -1e-12
        series_checks.append({'N': N, 'uniform_LER_tail_bound': uniform_tail,
                              'max_actual_remainder': float(np.max(true-partial))})
    files = [Path(__file__), LAB/'scripts/current_oracle.py', ROOT/'src/herald_decoder/lattice_model.py']
    out = {'status': 'passed', 'scope': 'Exact finite identities and analytic path limit; no identified 2D CFT or critical noise rate.',
           'kernel_checks': kernels, 'square_sector_checks': square, 'replica_integral_max_error': quad_max,
           'path_limits': paths, 'series_checks': series_checks,
           'square_genie_bounds': [{'L': L, 'p': .3, 'q': q, 'LER_lower_bound': square_genie_bound(L, .3, q)}
                                   for L in (5, 7, 9) for q in (.5, .75, .97, 1.)],
           'conditional_gaussian_annulus': [gaussian_annulus_check(A) for A in (.2, 1., 2*np.pi, 10.)],
           'source_sha256': {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}}
    target = LAB/'results/replica-boundary-theory-2026-09-18.json'
    target.write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps({'status': out['status'], 'channel_cases': len(grid), 'replica_integral_max_error': quad_max,
                      'example_p03q075': square[5], 'path_p03': paths[4:8], 'series_checks': series_checks}, indent=2))


if __name__ == '__main__':
    main()
