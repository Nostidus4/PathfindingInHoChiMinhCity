"""WP5 standalone smoke demo; production CLI/map belong to WP6."""
import argparse
import json
from pathlib import Path

from .algorithms import astar, dijkstra
from .examples.mock_data import MODES, build_mock

from .validation import check_admissibility, check_consistency, check_fifo, compare_routes

def parse_time(value):
    try:
        parts = value.split(':')
        if len(parts) not in (2, 3):
            raise ValueError()
        hour, minute = int(parts[0]), int(parts[1])
        second = int(parts[2]) if len(parts) == 3 else 0
        if not (0 <= hour < 24 and 0 <= minute < 60 and 0 <= second < 60):
            raise ValueError()
        return hour*3600 + minute*60 + second
    except ValueError:
        # Fail with ValueError so callers and tests can assert this specific error type
        raise ValueError('Time must be HH:MM or HH:MM:SS') from None

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', default='S')
    parser.add_argument('--goal', default='G')
    parser.add_argument('--time', type=parse_time, default=28800)
    parser.add_argument('--heuristic', choices=MODES, default='dynamic_ub')
    parser.add_argument('--trace', action='store_true')
    parser.add_argument('--validate', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    graph, traffic, heuristic = build_mock()
    try:
        result = astar(graph, args.start, args.goal, args.time, traffic.edge_cost,
                       heuristic, args.heuristic, args.trace)
        oracle = dijkstra(graph, args.start, args.goal, args.time, traffic.edge_cost)
        payload = {'fixture': 'synthetic WP5 mock',
                   'route': None if result is None else result.to_dict(),
                   'dijkstra': None if oracle is None else oracle.to_dict()}
        if args.validate:
            times = range(0, 86401, 900)
            payload['fifo'] = check_fifo(graph, times, traffic.edge_cost).to_dict()
            payload['validation'] = {}
            for mode in MODES:
                payload['validation'][mode] = {
                    'admissibility': check_admissibility(graph, graph.nodes, graph.nodes,
                        times, traffic.edge_cost, heuristic, mode).to_dict(),
                    'consistency': check_consistency(graph, graph.nodes, times,
                        traffic.edge_cost, heuristic, mode).to_dict(),
                    'optimality': compare_routes(graph, [('S', 'G', args.time)],
                        traffic.edge_cost, heuristic, [mode]).to_dict()}
        output = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding='utf-8')
        print(output)
    except (ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))

if __name__ == '__main__':
    main()
