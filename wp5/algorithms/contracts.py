"""Structural interfaces: existing WP2/WP4 classes need no inheritance."""
from typing import Protocol
from collections.abc import Hashable, Iterable, Collection, Callable

import math

class RoadSegment(Protocol):
    id: Hashable
    u: Hashable
    v: Hashable
    length_m: float

class Graph(Protocol):
    nodes: Collection[Hashable]
    def get_neighbors(self, node_id: Hashable) -> Iterable[RoadSegment]: ...

EdgeCost = Callable[[RoadSegment, float], float]
Heuristic = Callable[[Hashable, Hashable, float, str], float]

def nonnegative(value, name, *, allow_infinity=False):
    value = float(value)
    if math.isnan(value) or value < 0 or (not allow_infinity and not math.isfinite(value)):
        suffix = 'not NaN' if allow_infinity else 'finite'
        raise ValueError(f'{name} must be nonnegative and {suffix}')
    return value

def check_query(graph, start, goal, departure_time):
    nodes = set(graph.nodes)
    if start not in nodes or goal not in nodes:
        raise ValueError('start and goal must belong to graph.nodes')
    return nonnegative(departure_time, 'departure_time')

def checked_edge(graph, edge, current):
    if edge.u != current or edge.v not in graph.nodes:
        raise ValueError('get_neighbors must return outgoing edges with known endpoints')
    nonnegative(edge.length_m, 'edge.length_m')
