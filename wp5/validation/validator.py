"""Sampled checks are evidence on supplied states, not mathematical proofs."""
import math
from dataclasses import dataclass, field, asdict
from ..algorithms import astar, dijkstra
from ..algorithms.contracts import nonnegative, checked_edge

@dataclass
class ValidationReport:
    check: str
    checked: int = 0
    skipped: int = 0
    violations: list[dict] = field(default_factory=list)
    @property
    def valid(self):
        return not self.violations
    def to_dict(self):
        return {'valid': self.valid, **asdict(self)}

def _tol(tolerance):
    return nonnegative(tolerance, 'tolerance')

def check_admissibility(graph, nodes, goals, times, edge_cost, heuristic,
                        mode='dynamic_ub', tolerance=1e-6):
    report = ValidationReport('admissibility')
    tolerance = _tol(tolerance)
    nodes, goals, times = list(nodes), list(goals), list(times)
    for goal in goals:
        for node in nodes:
            for t in times:
                h = nonnegative(heuristic(node, goal, t, mode), 'heuristic')
                optimal = dijkstra(graph, node, goal, t, edge_cost)
                if optimal is None:
                    report.skipped += 1
                    continue
                report.checked += 1
                actual = optimal.total_travel_time
                if h > actual + tolerance:
                    report.violations.append({
                        'node': node,
                        'goal': goal,
                        'time': t,
                        'heuristic': h,
                        'optimal': actual,
                        'excess': h - actual,
                    })
    return report

def check_consistency(graph, goals, times, edge_cost, heuristic,
                      mode='dynamic_ub', tolerance=1e-6):
    report = ValidationReport('consistency')
    tolerance = _tol(tolerance)
    goals, times = list(goals), list(times)
    for goal in goals:
        for t in times:
            nonnegative(t, 'time')
            h_goal = nonnegative(heuristic(goal, goal, t, mode), 'heuristic')
            report.checked += 1
            if h_goal > tolerance:
                report.violations.append({
                    'goal': goal,
                    'time': t,
                    'reason': 'h(goal,t) != 0',
                    'h': h_goal,
                })
            for u in graph.nodes:
                for edge in graph.get_neighbors(u):
                    checked_edge(graph, edge, u)
                    c = nonnegative(edge_cost(edge, t), 'edge_cost', allow_infinity=True)
                    if math.isinf(c):
                        report.skipped += 1
                        continue
                    hu = nonnegative(heuristic(u, goal, t, mode), 'heuristic')
                    hv = nonnegative(heuristic(edge.v, goal, t+c, mode), 'heuristic')
                    report.checked += 1
                    if hu > c + hv + tolerance:
                        report.violations.append({
                            'edge_id': edge.id,
                            'u': u,
                            'v': edge.v,
                            'goal': goal,
                            'time': t,
                            'h_u': hu,
                            'cost': c,
                            'h_v': hv,
                            'excess': hu - c - hv,
                        })
    return report

def check_fifo(graph, times, edge_cost, tolerance=1e-6):
    """Compare adjacent departures on a sorted unique sample grid.

    +inf is treated as an infinite arrival: reopening after a blocked time
    is a violation for this no-waiting, single-label engine.
    """
    report = ValidationReport('fifo')
    tolerance = _tol(tolerance)
    times = sorted(set(nonnegative(t, 'time') for t in times))
    if len(times) < 2:
        raise ValueError('FIFO check needs at least two distinct times')
    for u in graph.nodes:
        for edge in graph.get_neighbors(u):
            checked_edge(graph, edge, u)
            previous = None
            for t in times:
                arrival = t + nonnegative(edge_cost(edge, t), 'edge_cost', allow_infinity=True)
                if previous is not None:
                    report.checked += 1
                    pt, pa = previous
                    if arrival + tolerance < pa:
                        report.violations.append({
                            'edge_id': edge.id,
                            't1': pt,
                            't2': t,
                            'arrival1': pa,
                            'arrival2': arrival,
                        })
                previous = t, arrival
    return report

def compare_routes(graph, queries, edge_cost, heuristic, modes, tolerance=1e-6):
    report = ValidationReport('optimality')
    tolerance = _tol(tolerance)
    modes = list(modes)
    for start, goal, t in queries:
        oracle = dijkstra(graph, start, goal, t, edge_cost)
        for mode in modes:
            result = astar(graph, start, goal, t, edge_cost, heuristic, mode)
            report.checked += 1
            mismatch = (oracle is None) != (result is None)
            if oracle is not None and result is not None:
                mismatch = abs(result.total_travel_time - oracle.total_travel_time) > tolerance
            if mismatch:
                report.violations.append({
                    'start': start,
                    'goal': goal,
                    'time': t,
                    'mode': mode,
                    'astar_cost': None if result is None else result.total_travel_time,
                    'dijkstra_cost': None if oracle is None else oracle.total_travel_time,
                    'astar_path': None if result is None else result.path,
                    'dijkstra_path': None if oracle is None else oracle.path,
                })
    return report
