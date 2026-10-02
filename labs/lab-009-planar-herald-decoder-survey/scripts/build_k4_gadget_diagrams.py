"""Reproduce the explanatory K4 diagrams, separate from benchmark figures."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrowPatch
from matplotlib.text import Text
import numpy as np

LAB = Path(__file__).resolve().parents[1]
REPO = LAB.parents[1]
sys.path.insert(0, str(REPO/'src'))
from herald_decoder._planar import face_cycles, pfaffian_orientation

BLUE, ORANGE, PURPLE = '#1477b5', '#bd661d', '#8454ac'
GREEN, INK, GRAY = '#19845b', '#203142', '#c5cbd1'
PORTS = np.array([[0., 1.], [-np.sqrt(3)/2, -.5], [np.sqrt(3)/2, -.5]])
CENTER = np.zeros(2)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 12,
                     'text.color': INK, 'mathtext.default': 'regular',
                     'svg.fonttype': 'none', 'svg.hashsalt': 'lab009-k4-gadget',
                     'pdf.fonttype': 42})


def segment(ax, u, v, color, width=2.5, style='-', zorder=2):
    ax.plot([u[0], v[0]], [u[1], v[1]], color=color, lw=width,
            ls=style, solid_capstyle='round', zorder=zorder)


def label(ax, x, y, text, **kwargs):
    box = kwargs.pop('bbox', {'facecolor': 'white', 'edgecolor': 'none', 'pad': 1.2})
    return ax.text(x, y, text, ha='center', va='center', zorder=6,
                   bbox=box, **kwargs)


def node(ax, xy, text=None, occupied=False, radius=.058):
    ax.add_patch(Circle(xy, radius, facecolor=BLUE if occupied else 'white',
                       edgecolor=BLUE if occupied else INK, lw=1.8, zorder=5))
    if text:
        label(ax, xy[0], xy[1]-.23, text, bbox=None)


def setup(ax, title, xlim=(-1.85, 1.85), ylim=(-1.8, 2.05)):
    ax.set_aspect('equal')
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis('off')
    ax.set_title(title, fontsize=15, fontweight='bold', pad=12)


def topology(ax, ports=PORTS, center=CENTER, zero_triangles=False):
    for i, j in [(0, 1), (0, 2), (1, 2)]:
        zero = zero_triangles and (i, j) != (1, 2)
        segment(ax, ports[i], ports[j], GRAY if zero else PURPLE,
                width=1.5 if zero else 2.5, style='--' if zero else '-')
    for p in ports:
        segment(ax, center, p, ORANGE)


def construction():
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 6.4))
    setup(axes[0], 'Original trivalent site')
    setup(axes[1], r'Planar $K_4$: four nodes, six edges')
    for i, p in enumerate(PORTS):
        end = 1.72*p
        segment(axes[0], CENTER, end, BLUE)
        node(axes[0], end)
        label(axes[0], *(1.1*p + np.array([.21, 0.])), rf'$z_{i+1},\ \rho_{i+1}$')
    node(axes[0], CENTER, r'$v$', radius=.085)
    label(axes[0], 0, -.99, r'Local site factor $\phi_v^r(z_1,z_2,z_3)$', fontsize=12)
    label(axes[0], 0, -1.35, r'Even entries: $(\phi_{000},\phi_{011},\phi_{101},\phi_{110})$', fontsize=11)
    axes[1].add_patch(Circle(CENTER, 1.08, fill=False, ec=GRAY, ls=':', lw=1.5))
    topology(axes[1])
    for i, p in enumerate(PORTS):
        segment(axes[1], p, 1.72*p, BLUE)
        node(axes[1], p)
        label(axes[1], *(p + np.array([-.23 if i != 2 else .23, .055])), rf'$p_{i+1}$', bbox=None)
        label(axes[1], *(1.60*p + np.array([.16 if i == 0 else 0, -.13 if i else 0])), rf'$\rho_{i+1}$', color=BLUE)
    node(axes[1], CENTER, r'$c$')
    for x, y, text in [(0, .50, r'$W_{c1}$'),
                       (-.43, -.25, r'$W_{c2}$'), (.43, -.25, r'$W_{c3}$')]:
        label(axes[1], x, y, text, color=ORANGE, fontsize=11)
    for x, y, text in [(-.58, .33, r'$W_{12}$'), (.58, .33, r'$W_{13}$'), (0, -.65, r'$W_{23}$')]:
        label(axes[1], x, y, text, color=PURPLE)
    label(axes[1], 0, -1.13, r'$W_{c1}=\phi_{011},\ W_{c2}=\phi_{101},\ W_{c3}=\phi_{110}$', fontsize=10)
    label(axes[1], 0, -1.48, r'$W_{c1}W_{23}+W_{c2}W_{13}+W_{c3}W_{12}=\phi_{000}$', fontsize=10)
    fig.add_artist(FancyArrowPatch((.47, .55), (.535, .55), transform=fig.transFigure,
                                  arrowstyle='-|>', mutation_scale=20, color=INK, lw=1.5))
    fig.legend(handles=[Line2D([], [], color=BLUE, lw=3, label='External wire: edge prior'),
                        Line2D([], [], color=ORANGE, lw=3, label='Spoke weight W_ci'),
                        Line2D([], [], color=PURPLE, lw=3, label='Triangle weight W_ij')],
               loc='lower center', ncol=3, frameon=False, fontsize=11)
    fig.subplots_adjust(top=.87, bottom=.12, left=.03, right=.97, wspace=.12)
    return fig


MATCHINGS = {
    '000': [(0, 3), (1, 2)], '011': [(0, 3)],
    '101': [(1, 3)], '110': [(2, 3)],
}
PATTERNS = ['000', '011', '101', '110']


def herald_signature(reference, herald, q):
    """Literal local herald likelihoods, evaluated exactly for a rational q."""
    values = []
    for pattern in PATTERNS:
        count = sum(int(r) ^ int(z) for r, z in zip(reference, pattern))
        probability = q if count >= 2 else Fraction(0)
        values.append(probability if herald else 1-probability)
    return tuple(values)


def solution_family_checks():
    """Enumerate actual internal matchings for pivots and distributed weights."""
    checked = []
    records = [('000', 0, Fraction(3, 5)), ('011', 1, Fraction(3, 5)),
               ('011', 0, Fraction(1)), ('001', 0, Fraction(1))]
    for reference, herald, q in records:
        signature = herald_signature(reference, herald, q)
        positive = [i for i, f in enumerate(signature[1:]) if f > 0]
        allocations = [{i: Fraction(int(i == pivot)) for i in positive} for pivot in positive]
        allocations.append({i: Fraction(1, len(positive)) for i in positive})
        for allocation in allocations:
            edges = {(i, 3): Fraction(signature[i+1]) for i in range(3)}
            opposite = [(1, 2), (0, 2), (0, 1)]
            for i in range(3):
                # Test the free-edge claim with a nonzero value when its coefficient is zero.
                edges[opposite[i]] = (Fraction(signature[0])*allocation[i]/signature[i+1]
                                      if i in positive else Fraction(4, 3))
            def visit(nodes):
                if not nodes:
                    return Fraction(1)
                i, *others = nodes
                return sum((edges.get(tuple(sorted((i, j))), Fraction(0))
                            * visit([k for k in others if k != j]) for j in others), Fraction(0))
            expected = dict(zip(PATTERNS, signature))
            for bits in itertools.product((0, 1), repeat=3):
                pattern = ''.join(map(str, bits))
                nodes = [i for i in range(3) if not bits[i]] + [3]
                assert visit(nodes) == expected.get(pattern, 0), (signature, allocation, bits)
            checked.append({'reference': reference, 'herald': herald, 'q': str(q),
                            'site_weights': [str(value) for value in signature],
                            'allocation': {str(i+1): str(a) for i, a in allocation.items()},
                            'all_eight_signatures_exact': True})
    return checked


def matching_cases():
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 9.0))
    signature = herald_signature('000', 0, Fraction(3, 5))
    values = [r'$0.4\times2.5=1=\phi_{000}$',
              r'$0.4=\phi_{011}$', r'$0.4=\phi_{101}$', r'$0.4=\phi_{110}$']
    xyz = np.vstack([PORTS, CENTER])
    for ax, (bits, edges), value, weight in zip(axes.flat, MATCHINGS.items(), values, signature):
        setup(ax, rf'$z={bits}$: $\phi_{{{bits}}}={float(weight):g}$', ylim=(-1.72, 1.85))
        topology(ax, zero_triangles=True)
        for i, p in enumerate(PORTS):
            selected = bits[i] == '1'
            segment(ax, p, 1.63*p, BLUE if selected else GRAY,
                    width=4 if selected else 1.5, style='-' if selected else ':')
            node(ax, p, occupied=selected)
            label(ax, *(p + np.array([-.28 if i != 2 else .28, .08])), rf'$p_{i+1}$', fontsize=11, bbox=None)
            label(ax, *(1.5*p + np.array([.21 if i == 0 else 0, -.20 if i else 0])),
                  rf'$z_{i+1}={bits[i]}$', fontsize=11, color=BLUE if selected else INK)
        for i, j in edges:
            segment(ax, xyz[i], xyz[j], GREEN, width=5, zorder=3)
        node(ax, CENTER, r'$c$')
        for x, y, text in [(0, .72, r'$W_{c1}=0.4$'),
                           (-.97, -.16, r'$W_{c2}=0.4$'), (.97, -.16, r'$W_{c3}=0.4$')]:
            label(ax, x, y, text, fontsize=12)
        label(ax, 0, -.78, r'$W_{23}=2.5$', fontsize=11)
        label(ax, -.97, .40, r'$W_{12}=0$', fontsize=10, color='#89929b')
        label(ax, .97, .40, r'$W_{13}=0$', fontsize=10, color='#89929b')
        label(ax, 0, -1.46, 'Internal weight: '+value, fontsize=12)
    fig.suptitle(r'Herald-channel example: $q=0.6,\ h_v=0,\ r_{\partial v}=000$'+'\n'+
                 r'$\phi_{000}=1,\quad \phi_{011}=\phi_{101}=\phi_{110}=0.4$',
                 fontsize=15, fontweight='bold', y=.975)
    fig.legend(handles=[Line2D([], [], color=GREEN, lw=4, label='Selected internal edge'),
                        Line2D([], [], color=BLUE, lw=4, label='Selected external wire'),
                        Line2D([], [], color=GRAY, lw=1.5, ls='--', label='Zero-weight triangle edge')],
               loc='lower center', ncol=3, frameon=False, fontsize=10)
    fig.subplots_adjust(top=.82, bottom=.095, left=.04, right=.96, hspace=.30, wspace=.12)
    return fig


def gluing():
    fig, ax = plt.subplots(figsize=(11.5, 6.1))
    setup(ax, 'Connect site gadgets along the original edges', xlim=(-3.7, 3.7), ylim=(-1.55, 2.15))
    # One port points inward; the other two point away from the shared wire.
    left = np.array([-2., 0.])
    right = np.array([2., 0.])
    directions = np.array([[1., 0.], [-.5, np.sqrt(3)/2], [-.5, -np.sqrt(3)/2]])
    pl, pr = left+.78*directions, right-.78*directions
    # Original sites and edge, above the expanded graph.
    segment(ax, left+[0, 1.55], right+[0, 1.55], BLUE)
    node(ax, left+[0, 1.55]); node(ax, right+[0, 1.55])
    label(ax, -2, 1.79, r'Original site $u$', fontsize=12)
    label(ax, 2, 1.79, r'Original site $v$', fontsize=12)
    label(ax, 0, 1.55, r'Original edge $e$: ratio $\rho_e$', color=BLUE)
    for x in [-2., 2.]:
        ax.add_patch(FancyArrowPatch((x, 1.33), (x, 1.00), arrowstyle='-|>',
                                    mutation_scale=15, color=INK, lw=1.4))
    for center, ports, sign in [(left, pl, 1), (right, pr, -1)]:
        ax.add_patch(Circle(center, .85, fill=False, ec=GRAY, ls=':', lw=1.5))
        topology(ax, ports, center)
        for i in [1, 2]:
            end = center + 1.65*(ports[i]-center)
            segment(ax, ports[i], end, BLUE)
        for p in ports:
            node(ax, p)
        node(ax, center)
        label(ax, center[0], -.23, r'$c_u$' if sign == 1 else r'$c_v$', fontsize=11, bbox=None)
        label(ax, center[0]-.44*sign, 0, r'$W_{23}^{(u)}$' if sign == 1 else r'$W_{23}^{(v)}$', color=PURPLE, fontsize=11)
        label(ax, center[0]+.43*sign, 0, r'$W_{c1}^{(u)}$' if sign == 1 else r'$W_{c1}^{(v)}$', color=ORANGE, fontsize=11)
        label(ax, center[0], -1.05, r'Site signature $\phi_u^r$' if sign == 1 else r'Site signature $\phi_v^r$', fontsize=12)
    segment(ax, pl[0], pr[0], BLUE, width=3.7)
    label(ax, 0, .30, r'One shared wire, weight $\rho_e$', color=BLUE, fontsize=13)
    label(ax, pl[0, 0]+.14, -.23, r'$p_{u,e}$', fontsize=11, bbox=None)
    label(ax, pr[0, 0]-.14, -.23, r'$p_{v,e}$', fontsize=11, bbox=None)
    label(ax, 0, -.64, r'$K_{p_{u,e},p_{v,e}}=\kappa_e\rho_e$', color=BLUE, fontsize=13)
    label(ax, 0, -1.40, 'Rows of K index ports and centers; orientation signs are assigned globally.', fontsize=12)
    fig.subplots_adjust(left=.03, right=.97, top=.86, bottom=.03)
    return fig


ORIENTATION_EDGES = np.array([(0, 1), (1, 2), (2, 0), (3, 0), (3, 1), (3, 2)])


def orientation_checks():
    """Check the illustrated arrows, odd vertex count and repeated bridge walks."""
    xyz = np.vstack([PORTS, CENTER])
    fixtures = [
        ('isolated-K4', xyz, ORIENTATION_EDGES),
        ('odd-size-triangle', PORTS, ORIENTATION_EDGES[:3]),
        ('K4-with-two-bridges', np.vstack([xyz, [-.13, .30], [1.17, -.55]]),
         np.vstack([ORIENTATION_EDGES, [3, 4], [2, 5]])),
    ]
    checked = []
    for name, positions, edges in fixtures:
        signs = pfaffian_orientation(positions, edges)
        _, cycles, areas = face_cycles(positions, edges)
        arrows = {tuple(edge if sign > 0 else edge[::-1]) for edge, sign in zip(edges, signs)}
        counts, repetitions = [], []
        for cycle in cycles:
            # face_cycles keeps the face on the left; reverse each occurrence.
            walk = [(int(edges[h//2, h%2]), int(edges[h//2, 1-h%2])) for h in cycle]
            counts.append(sum((v, u) in arrows for u, v in walk))
            repetitions.append(len(cycle)-len(set(cycle//2)))
        assert all(count % 2 == 1 for count, area in zip(counts, areas) if area > 0)
        outer = int(np.flatnonzero(areas < 0)[0])
        assert counts[outer] % 2 == (len(positions)-1) % 2
        if name == 'isolated-K4':
            assert signs.tolist() == [1]*6
            assert [count for count, area in zip(counts, areas) if area > 0] == [1]*3
            K = np.zeros((4, 4), dtype=int)
            for (i, j), sign in zip(edges, signs):
                K[i, j] = sign; K[j, i] = -sign
            coefficients = [int(K[0, 1]*K[2, 3]), -int(K[0, 2]*K[1, 3]),
                            int(K[0, 3]*K[1, 2])]
            assert coefficients == [-1]*3
        if name == 'K4-with-two-bridges':
            assert any(repeated > 0 for repeated, area in zip(repetitions, areas) if area > 0)
        checked.append({'fixture': name, 'vertices': len(positions), 'edges': edges.tolist(),
                        'signs_relative_to_stored_edges': signs.tolist(),
                        'bounded_face_clockwise_counts': [count for count, area in zip(counts, areas) if area > 0],
                        'outer_face_on_right_agreement_count': counts[outer],
                        'repeated_boundary_edge_occurrences': repetitions,
                        **({'pfaffian_matching_coefficients': coefficients} if name == 'isolated-K4' else {})})
    return checked


def orientation():
    fig, ax = plt.subplots(figsize=(8.5, 6.9))
    setup(ax, r'An isolated $K_4$: every bounded face is clockwise odd',
          xlim=(-1.45, 1.45), ylim=(-1.04, 1.42))
    xyz = np.vstack([PORTS, CENTER])
    for i, j in ORIENTATION_EDGES:
        color = ORANGE if i == 3 else PURPLE
        ax.add_patch(FancyArrowPatch(xyz[i], xyz[j], arrowstyle='-|>',
                                    mutation_scale=23, shrinkA=10, shrinkB=10,
                                    color=color, lw=2.8, zorder=2))
    for i, p in enumerate(PORTS):
        node(ax, p, radius=.052)
        offset = [0, .16] if i == 0 else [-.13 if i == 1 else .13, -.14]
        label(ax, *(p+offset), rf'$p_{i+1}$', fontsize=13, bbox=None)
    node(ax, CENTER, radius=.052)
    label(ax, 0, -.12, r'$c$', fontsize=13, bbox=None)
    for face in [(3, 0, 1), (3, 0, 2), (3, 1, 2)]:
        midpoint = xyz[list(face)].mean(axis=0)
        label(ax, *midpoint, '1 cw', fontsize=12, color=GREEN,
              bbox={'facecolor': '#ecf7f0', 'edgecolor': 'none', 'pad': 3})
    label(ax, 0, -.86, 'cw = arrows agreeing with a clockwise face walk', fontsize=11)
    fig.subplots_adjust(left=.04, right=.96, top=.87, bottom=.045)
    return fig


def main():
    fixture_path = LAB/'results/site-gadget-partition-review.json'
    fixture = json.loads(fixture_path.read_text())
    assert fixture['status'] == 'passed'
    # A physical herald record checks the diagram's products and site-entry labels.
    signature = herald_signature('000', 0, Fraction(3, 5))
    edge_weights = {(i, 3): signature[i+1] for i in range(3)}
    edge_weights[1, 2] = signature[0]/signature[1]
    expected = dict(zip(PATTERNS, signature))
    checks = []
    for bits, edges in MATCHINGS.items():
        coverage = [int(b) for b in bits] + [0]
        product = Fraction(1)
        for i, j in edges:
            coverage[i] += 1; coverage[j] += 1
            product *= edge_weights[i, j]
        assert coverage == [1]*4, (bits, coverage)
        assert product == expected[bits]
        checks.append({'relative_bits': bits, 'selected_internal_edges': edges,
                       'auxiliary_node_coverage': coverage, 'site_entry': 'phi_'+bits,
                       'physical_validation_weight': str(product)})
    outputs = []
    checked_orientations = orientation_checks()
    (LAB/'figures').mkdir(exist_ok=True)
    for name, build in [('k4-gadget-construction', construction),
                        ('k4-gadget-matchings', matching_cases),
                        ('k4-gadget-gluing', gluing),
                        ('k4-gadget-orientation', orientation)]:
        fig = build()
        # The wiki embeds figures at 80% of its text column, so use readable labels there.
        for item in fig.findobj(match=Text):
            item.set_fontsize(item.get_fontsize()*1.35)
        files = []
        for extension in ['png', 'svg', 'pdf']:
            file = LAB/f'figures/{name}.{extension}'
            metadata = {'CreationDate': None, 'ModDate': None} if extension == 'pdf' else None
            fig.savefig(file, dpi=180, facecolor='white', metadata=metadata)
            files.append({'path': str(file.relative_to(LAB)),
                          'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
        plt.close(fig)
        outputs.append({'name': name, 'files': files})
    receipt = {'status': 'passed', 'generated_at': datetime.now(timezone.utc).isoformat(),
               'generator_source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'partition_fixture': str(fixture_path.relative_to(LAB)),
               'partition_fixture_sha256': hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
               'illustration': 'Site entries phi_beta; all internal edges labeled W_ci or W_ij; pivot phi_011>0',
               'physical_validation_record': {'reference': '000', 'herald': 0, 'q': '3/5',
                                               'site_weights': [str(value) for value in signature]},
               'site_entry_order': ['phi_000', 'phi_011', 'phi_101', 'phi_110'],
               'notation': {'physical_edge': 'w_e(x_e)', 'physical_site': 'phi_v(x_incident)',
                            'relative_site': 'phi_v^r(z_incident)', 'relative_prior_ratio': 'rho_e',
                            'auxiliary_edge': 'W_ij'},
               'matching_checks': checks, 'solution_family_checks': solution_family_checks(),
               'orientation_checks': checked_orientations,
               'orientation_source': 'src/herald_decoder/_planar.py',
               'orientation_source_sha256': hashlib.sha256((REPO/'src/herald_decoder/_planar.py').read_bytes()).hexdigest(),
               'no_K4_solution_for_positive_000_only': True, 'figures': outputs,
               'semantics': {'external_occupation': 'z_i=1 covers port p_i externally',
                             'displayed_signature_weights': 'internal only; external priors multiply once per wire',
                             'orientation': 'first three figures are undirected; fourth is an isolated K4 orientation, not the glued global orientation',
                             'zero_edges': 'two triangle edges have zero weight only in the numerical example'},
               'scope': 'Explanatory schematics; no new benchmark samples or production geometry support.'}
    (LAB/'results/k4-gadget-diagrams.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({'status': 'passed', 'figures': len(outputs), 'matching_checks': len(checks)}))


if __name__ == '__main__':
    main()
