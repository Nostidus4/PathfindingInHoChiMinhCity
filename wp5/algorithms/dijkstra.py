"""Independent FIFO earliest-arrival Dijkstra oracle (no A* invocation)."""
import heapq
import itertools
import math
from time import perf_counter

from .contracts import check_query, checked_edge, nonnegative
from .result import RouteResult

def dijkstra(graph, start, goal, departure_time, edge_cost):
    began = perf_counter()
    departure_time = check_query(graph, start, goal, departure_time)
    counter = itertools.count()
    distances = {start: 0.0}
    parents = {}
    settled = set()
    queue = [(0.0, next(counter), start)]
    expanded = 0
    while queue:
        g, _, u = heapq.heappop(queue)
        if u in settled or g != distances[u]:
            continue
        settled.add(u)
        expanded += 1
        if u == goal:
            path, edges = [u], []
            while u != start:
                u, edge = parents[u]
                path.append(u)
                edges.append(edge)
            path.reverse()
            edges.reverse()
            return RouteResult(path, departure_time, departure_time + g, g,
                               sum(float(e.length_m) for e in edges), expanded,
                               perf_counter() - began, None, [e.id for e in edges])
        for edge in graph.get_neighbors(u):
            checked_edge(graph, edge, u)
            cost = nonnegative(
                edge_cost(edge, departure_time + g), 'edge_cost', allow_infinity=True)
            if math.isinf(cost):
                continue
            new_g = g + cost
            if not math.isfinite(new_g):
                raise ValueError('accumulated cost overflow')
            if edge.v not in settled and new_g < distances.get(edge.v, math.inf):
                distances[edge.v] = new_g
                parents[edge.v] = (u, edge)
                heapq.heappush(queue, (new_g, next(counter), edge.v))
    return None
