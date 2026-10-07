# Nối WP5 với WP2–WP4 và WP6

## Hợp đồng cần thống nhất

| Nguồn | Interface | Đơn vị / yêu cầu |
|---|---|---|
| WP2 | `graph.nodes` | Collection ID hashable, có membership và lặp được nhiều lần |
| WP2 | `graph.get_neighbors(u)` | Các outgoing edge, không tự thêm cạnh ngược |
| WP2 | `edge.id, edge.u, edge.v, edge.length_m` | ID cạnh duy nhất, length mét |
| WP3/WP4 | `edge_cost(edge, entry_time)` | Giây, không âm, hữu hạn hoặc +inf |
| WP4 | `heuristic(node, goal, arrival_time, mode)` | Giây, không âm, hữu hạn; goal = 0 |
| WP6 | `RouteResult.to_dict()` | Path, ETA, travel time, distance, expansion, runtime, trace, edge IDs |

TrafficProvider không bị hardcode trong engine. Tạo closure/bound method để đưa provider vào cost và heuristic.
Ví dụ minh họa bên dưới cần đổi tên module/method theo source nhóm (không phải import có sẵn):

```python
from algorithms import astar, dijkstra
from validation import check_fifo, check_admissibility, check_consistency, compare_routes

# graph = wp2.load_graph(...)
# traffic_provider = wp3.TrafficProvider(...)
# cost_model = wp4.CostModel(graph, traffic_provider)
# heuristic_model = wp4.HeuristicModel(graph, traffic_provider)
# edge_cost = cost_model.edge_cost
# heuristic = heuristic_model.heuristic

result = astar(graph, start, goal, departure_time,
               edge_cost=edge_cost, heuristic=heuristic,
               heuristic_mode='dynamic_ub', trace=True)
if result is None:
    print('Không có đường đi')
else:
    print(result.to_dict())
```

Nếu WP4 dùng tham số keyword-only `mode`, bọc adapter:

```python
heuristic = lambda node, goal, time, mode: wp4_h(node, goal, time, mode=mode)
```

Nếu WP2 dùng dict node, `graph.nodes` có thể chính là dict (lặp ra keys).
Nếu edge.v đang là object POI, adapter phải đổi về ID trùng graph.nodes.
Nếu graph hỗ trợ cạnh hai chiều, WP2 cung cấp riêng hai outgoing edges.
Nếu speed WP3 là km/h, WP4 đổi sang m/s trước `length_m / speed`.
Không sửa length bằng haversine: giữ chiều dài đường thật; haversine chỉ dùng heuristic.

## Quy trình kiểm chứng dữ liệu thật

1. Đóng băng snapshot traffic để các lần chạy dùng cùng dữ liệu.
2. WP2 kiểm tra length >= haversine và các endpoints hợp lệ.
3. Quét FIFO trên mọi edge: mốc 15 phút, bổ sung điểm sát boundary/profile breakpoint và lưới dày hơn.
4. Nếu FIFO PASS trên các mẫu, chạy admissibility/consistency trên nhiều goals/times.
5. So A* ở zero/static_vmax/dynamic_ub với oracle bằng `compare_routes`.
6. Chạy dynamic_weighted trên danh sách query; `violations` lưu những query có cost khác oracle.
7. Chuyển RouteResult và các report cho WP6; WP6 vẽ theo edge_ids/geometry.

```python
fifo = check_fifo(graph, range(0, 86401, 900), edge_cost)
if not fifo.valid:
    raise ValueError(f'FIFO violations: {fifo.violations[:3]}')

admissibility = check_admissibility(graph, graph.nodes, chosen_goals,
                                   times, edge_cost, heuristic, 'dynamic_ub')
consistency = check_consistency(graph, chosen_goals, times,
                               edge_cost, heuristic, 'dynamic_ub')
optimality = compare_routes(graph, queries, edge_cost, heuristic,
                           ['zero', 'static_vmax', 'dynamic_ub'])
weighted_cases = compare_routes(graph, queries, edge_cost, heuristic,
                               ['dynamic_weighted']).violations
```

`check_admissibility` chạy một Dijkstra cho mỗi node×goal×time, nên bắt đầu với tập goal nhỏ.
Không kết luận consistency/admissibility phổ quát từ sample PASS; dùng chứng minh WP4.
V_ub phải bao phủ tương lai thực sự, kể cả phần ngoài window được clamp nếu route đi qua biên.

## Ghép thư mục

Copy `algorithms/` và `validation/` vào root Python project nhóm.
Nếu nhóm dùng `src/`, đặt hai thư mục dưới src và chạy với src trên PYTHONPATH hoặc cài package của nhóm.
Import trong validation hiện dùng `from algorithms ...`; sửa nếu nhóm chọn namespace khác.
Các mock/demo/tests là tài liệu để chạy độc lập, không bắt buộc đưa vào production UI.
