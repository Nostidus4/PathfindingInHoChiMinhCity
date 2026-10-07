"""Time-dependent A*: requires FIFO travel times and deterministic providers.

Optimality requires an admissible heuristic (including h(goal,t)=0).
Inconsistent heuristics are supported through reopening. Weighted heuristics
are accepted for experiments, but do not carry an optimality guarantee.
"""
from dataclasses import dataclass
import heapq
import itertools
import math
from time import perf_counter

from .contracts import check_query, checked_edge, nonnegative
from .result import RouteResult

@dataclass(frozen=True)
class _Label:
    node: object
    g: float
    h: float
    parent: object = None
    edge: object = None

def _reconstruct(label):
    nodes, edges = [], []
    while label is not None:
        nodes.append(label.node)
        if label.edge is not None:
            edges.append(label.edge)
        label = label.parent
    nodes.reverse()
    edges.reverse()
    return nodes, edges

def astar(graph, start, goal, departure_time, edge_cost, heuristic,
          heuristic_mode='dynamic_ub', trace=False):
    """Return RouteResult, or None if unreachable. No waiting actions are added.

    edge_cost(edge, entry_time) returns seconds; +inf marks a blocked edge.
    heuristic(node, goal, arrival_time, mode) returns nonnegative finite seconds.
    Node IDs can be arbitrary hashable values. Heap ties never compare IDs.
    expanded_nodes counts live pops, including goal and repeated expansions.
    trace includes a post-relaxation snapshot of the active open set.
    """
    began = perf_counter()
    departure_time = check_query(graph, start, goal, departure_time)
    def h_at(node, time):
        h = nonnegative(heuristic(node, goal, time, heuristic_mode), 'heuristic')
        if node == goal and h != 0:
            raise ValueError('heuristic(goal, goal, t) must be zero')
        return h
    serial = itertools.count()
    first = _Label(start, 0.0, h_at(start, departure_time))
    heap = [(first.h, next(serial), first)]
    best = {start: first}
    closed = set()
    expanded = 0
    records = [] if trace else None
    while heap:
        f, _, current = heapq.heappop(heap)
        if best.get(current.node) is not current or current.node in closed:
            continue
        closed.add(current.node)
        expanded += 1
        time = departure_time + current.g
        relaxed = []
        if current.node != goal:
            for edge in graph.get_neighbors(current.node):
                checked_edge(graph, edge, current.node)
                cost = nonnegative(edge_cost(edge, time), 'edge_cost', allow_infinity=True)
                if math.isinf(cost):
                    continue
                candidate = current.g + cost
                if not math.isfinite(candidate):
                    raise ValueError('accumulated cost overflow')
                old = best.get(edge.v)
                if old is None or candidate < old.g:
                    h = h_at(edge.v, departure_time + candidate)
                    label = _Label(edge.v, candidate, h, current, edge)
                    reopened = edge.v in closed
                    closed.discard(edge.v)
                    best[edge.v] = label
                    heapq.heappush(heap, (candidate + h, next(serial), label))
                    if trace:
                        relaxed.append({'edge_id': edge.id, 'node': edge.v,
                                        'cost': cost, 'g': candidate, 'reopened': reopened})
        if trace:
            active = [(pf, seq, lab) for pf, seq, lab in heap
                      if best.get(lab.node) is lab and lab.node not in closed]
            active.sort(key=lambda item: (item[0], item[1]))
            records.append({'step': expanded, 'node': current.node, 'g': current.g,
                            'h': current.h, 'f': f, 'arrival_time': time,
                            'relaxed': relaxed, 'open_set': [
                                {'node': lab.node, 'g': lab.g, 'h': lab.h,
                                 'f': pf, 'arrival_time': departure_time + lab.g}
                                for pf, _, lab in active]})
        if current.node == goal:
            nodes, edges = _reconstruct(current)
            return RouteResult(nodes, departure_time, time, current.g,
                               sum(float(e.length_m) for e in edges), expanded,
                               perf_counter() - began, records, [e.id for e in edges])
    return None
