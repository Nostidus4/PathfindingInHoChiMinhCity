"""Small synthetic fixture, NOT the group's >=100 POI road dataset.

Traffic is a mock, not a Greenshields implementation: WP3/WP4 replace it.
Its speed decreases smoothly, so arrival t+c(e,t) is increasing analytically.
"""
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt

MODES = ('zero', 'static_vmax', 'dynamic_ub', 'dynamic_weighted')

@dataclass(frozen=True)
class POI:
    id: str
    lat: float
    lon: float

@dataclass(frozen=True)
class Edge:
    id: str
    u: str
    v: str
    length_m: float

class MockGraph:
    def __init__(self, pois, edges):
        self.pois = {p.id: p for p in pois}
        self.nodes = tuple(self.pois)
        self.edges = tuple(edges)
        self.adjacency = {n: [] for n in self.nodes}
        for e in edges:
            if e.u not in self.adjacency or e.v not in self.adjacency:
                raise ValueError('Unknown endpoint')
            self.adjacency[e.u].append(e)
    def get_neighbors(self, node_id):
        return self.adjacency[node_id]


def haversine(a, b):
    la, lb = radians(a.lat), radians(b.lat)
    dlat, dlon = lb-la, radians(b.lon-a.lon)
    x = sin(dlat/2)**2 + cos(la)*cos(lb)*sin(dlon/2)**2
    return 6371000 * 2 * asin(sqrt(min(1, max(0, x))))

class MockTraffic:
    """m/s, seconds since midnight. Clamp outside the [0,86400] window."""
    vmax = 15.0
    def speed(self, edge, time):
        time = min(86400.0, max(0.0, time))
        return self.vmax / (1 + time/86400.0)
    def upper_bound(self, time):
        # All mock edges share this decreasing profile: future suffix max = now.
        return self.speed(None, time)
    def average_speed(self, time):
        return self.speed(None, time)
    def edge_cost(self, edge, time):
        return edge.length_m / self.speed(edge, time)

class MockHeuristic:
    def __init__(self, graph, traffic, weight=4.0):
        if weight <= 1:
            raise ValueError('weight must exceed one')
        self.graph, self.traffic, self.weight = graph, traffic, weight
    def __call__(self, node, goal, time, mode):
        if mode not in MODES:
            raise ValueError(f'Unknown mode: {mode}')
        d = haversine(self.graph.pois[node], self.graph.pois[goal])
        if mode == 'zero':
            return 0.0
        if mode == 'static_vmax':
            return d/self.traffic.vmax
        if mode == 'dynamic_ub':
            return d/self.traffic.upper_bound(time)
        return self.weight*d/self.traffic.average_speed(time)


def build_mock():
    pois = [POI(n, 10.77, 106.69 + i*0.001)
            for i, n in enumerate(('S', 'A', 'G', 'B', 'C', 'U'))]
    lookup = {p.id: p for p in pois}
    def edge(id, u, v, factor=1):
        return Edge(id, u, v, haversine(lookup[u], lookup[v])*factor)
    edges = [edge('SA', 'S', 'A'), edge('AG', 'A', 'G'),
             edge('SG_detour', 'S', 'G', 1.5),
             edge('SB', 'S', 'B', 2), edge('BC', 'B', 'C'),
             edge('CG', 'C', 'G', 2), edge('GS', 'G', 'S', 2)]
    graph = MockGraph(pois, edges)
    traffic = MockTraffic()
    return graph, traffic, MockHeuristic(graph, traffic)
