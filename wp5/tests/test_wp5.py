import math
import random
import unittest

from ..algorithms import astar, dijkstra
from ..demo import parse_time
from ..examples.mock_data import POI, Edge, MockGraph, build_mock
from ..validation import (
    check_admissibility,
    check_consistency,
    check_fifo,
    compare_routes,
)

class WP5Tests(unittest.TestCase):
    def setUp(self):
        self.g, self.traffic, self.h = build_mock()
        self.cost = self.traffic.edge_cost
    def test_all_pairs_all_97_times(self):
        queries = [(u,v,t) for u in self.g.nodes for v in self.g.nodes for t in range(0,86401,900)]
        r = compare_routes(self.g, queries, self.cost, self.h,
                           ['zero','static_vmax','dynamic_ub'])
        self.assertTrue(r.valid, r.violations[:1])
        self.assertEqual(r.checked, 10476)
    def test_admissibility_all_modes(self):
        for mode in ['zero','static_vmax','dynamic_ub']:
            r = check_admissibility(self.g, self.g.nodes, self.g.nodes,
                range(0,86401,900), self.cost, self.h, mode)
            self.assertTrue(r.valid, r.violations[:1])
            self.assertGreater(r.checked, 0)
            self.assertGreater(r.skipped, 0)
    def test_consistency_all_modes(self):
        for mode in ['zero','static_vmax','dynamic_ub']:
            r = check_consistency(self.g, self.g.nodes, range(0,86401,900), self.cost, self.h, mode)
            self.assertTrue(r.valid, r.violations[:1])
    def test_weighted_counterexample(self):
        a = astar(self.g,'S','G',28800,self.cost,self.h,'dynamic_weighted')
        d = dijkstra(self.g,'S','G',28800,self.cost)
        self.assertEqual(a.path, ['S','G'])
        self.assertEqual(d.path, ['S','A','G'])
        self.assertGreater(a.total_travel_time, d.total_travel_time)
        self.assertFalse(check_admissibility(self.g,['S','A'],['G'],[28800],self.cost,self.h,'dynamic_weighted').valid)
        self.assertFalse(check_consistency(self.g,['G'],[28800],self.cost,self.h,'dynamic_weighted').valid)
    def test_fifo_dense_grid_and_clamp(self):
        self.assertTrue(check_fifo(self.g, range(0,90001,60),self.cost).valid)
    def test_fifo_detects_drop(self):
        self.assertFalse(check_fifo(self.g,[0,1],lambda e,t: 100 if t==0 else 1).valid)
    def test_departure_changes_cost_and_heuristic(self):
        a = dijkstra(self.g,'S','G',0,self.cost)
        b = dijkstra(self.g,'S','G',28800,self.cost)
        self.assertGreater(b.total_travel_time,a.total_travel_time)
        self.assertNotEqual(self.h('S','G',0,'dynamic_ub'),self.h('S','G',28800,'dynamic_ub'))
    def test_cost_called_at_arrival(self):
        calls=[]
        def cost(e,t):
            calls.append((e.id,t))
            return self.cost(e,t)
        r=astar(self.g,'S','G',28800,cost,self.h)
        self.assertIn(('AG',28800+self.cost(self.g.edges[0],28800)), calls)
        self.assertEqual(r.estimated_arrival_time,28800+r.total_travel_time)
    def test_no_path(self):
        self.assertIsNone(astar(self.g,'S','U',0,self.cost,self.h))
        self.assertIsNone(dijkstra(self.g,'S','U',0,self.cost))
    def test_start_equals_goal(self):
        r=astar(self.g,'A','A',0,self.cost,self.h,trace=True)
        self.assertEqual(r.path,['A'])
        self.assertEqual(r.total_travel_time,0)
        self.assertEqual(r.total_distance,0)
        self.assertEqual(r.trace[0]['open_set'],[])
    def test_trace_and_distance(self):
        r=astar(self.g,'S','G',0,self.cost,self.h,trace=True)
        self.assertEqual(len(r.trace),r.expanded_nodes)
        self.assertEqual(r.edge_ids,['SA','AG'])
        self.assertAlmostEqual(r.total_distance,sum(e.length_m for e in self.g.edges[:2]))
        for entry in r.trace:
            self.assertAlmostEqual(entry['f'],entry['g']+entry['h'])
            self.assertIn('open_set',entry)
        self.assertIsNone(astar(self.g,'S','G',0,self.cost,self.h).trace)
    def test_invalid_inputs(self):
        for algo in [astar, dijkstra]:
            for value in [-1, float('nan')]:
                def make_cost(v):
                    def cost(e, t):
                        return v
                    return cost
                args = (self.g, 'S', 'G', 0, make_cost(value))
                with self.assertRaises(ValueError):
                    algo(*args, self.h) if algo is astar else algo(*args)
        with self.assertRaises(ValueError):
            astar(self.g,'X','G',0,self.cost,self.h)
        with self.assertRaises(ValueError):
            astar(self.g,'S','G',0,self.cost,lambda *args: 1)
        self.assertIsNone(astar(self.g,'S','G',0,lambda e,t:math.inf,self.h))
    def test_heap_ties_parallel_edges_and_stale_entries(self):
        # Mixed hashable IDs cannot be ordered; parallel routes require exact edges.
        g=MockGraph([POI(n,0,0) for n in ['S',1,('a',),'G']],
            [Edge('slow','S',1,10),Edge('fast','S',1,1),Edge('tie','S',('a',),1),
             Edge('goal',1,'G',20)])
        for algo in [astar,dijkstra]:
            args=(g,'S','G',0,lambda e,t:e.length_m)
            r=algo(*args,lambda *args:0) if algo is astar else algo(*args)
            self.assertEqual(r.edge_ids,['fast','goal'])
            self.assertEqual(r.total_distance,21)
            self.assertEqual(r.expanded_nodes,4)
    def test_reopening_with_admissible_inconsistent_h(self):
        g=MockGraph([POI(n,0,0) for n in 'SBAG'],
            [Edge('SA','S','A',5),Edge('SB','S','B',1),Edge('BA','B','A',1),Edge('AG','A','G',10)])
        def h(n, *args):
            return {'S': 0, 'B': 10, 'A': 0, 'G': 0}[n]
        r=astar(g,'S','G',0,lambda e,t:e.length_m,h,trace=True)
        self.assertEqual(r.path,['S','B','A','G'])
        self.assertEqual(r.total_travel_time,12)
        self.assertTrue(any(x['reopened'] for s in r.trace for x in s['relaxed']))
    def test_random_fifo_graphs_against_independent_oracle(self):
        rng=random.Random(2026)
        for _ in range(20):
            edges = [Edge(f'{u}-{v}', u, v, rng.randint(1, 100)) for u in range(8)
                     for v in range(8) if u != v and rng.random() < .3]
            g = MockGraph([POI(n, 0, 0) for n in range(8)], edges)
            def c(e, t):
                return e.length_m * (1 + t / 86400)
            r = compare_routes(
                g,
                [(u, v, t) for u in g.nodes for v in g.nodes for t in [0, 28800]],
                c,
                lambda *args: 0,
                ['zero'],
            )
            self.assertTrue(r.valid, r.violations[:1])
    def test_zero_cost_cycle(self):
        g=MockGraph([POI(n,0,0) for n in 'SAG'],
            [Edge('SA','S','A',0),Edge('AS','A','S',0),Edge('AG','A','G',1)])
        r=astar(g,'S','G',0,lambda e,t:e.length_m,lambda *args:0)
        self.assertEqual(r.total_travel_time,1)
    def test_cli_time(self):
        self.assertEqual(parse_time('08:30:15'),30615)
        self.assertEqual(parse_time('08:00'),28800)
        with self.assertRaises(ValueError):
            parse_time('25:00')

if __name__=='__main__':
    unittest.main()
