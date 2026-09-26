# Dựng graph (M3, WP2)

> Owner: **P2** · Review: P1 · Code: `src/graph/`, `scripts/build_graph.py`

## 1. Quyết định D3: Curated POI graph with road-geometry edges ✅

- **Node** là các POI đã chọn (khoảng 150, tối thiểu 100). Theo định nghĩa của nhóm, POI có thể là
  landmark, ngã tư hoặc nút giao, nên tập node này đủ điều kiện gọi là "POI".
- **Edge** là kết nối đi được trực tiếp giữa hai POI kề nhau. Độ dài lấy từ đường thật trên OSM, kèm
  polyline để vẽ route bám theo đường trên bản đồ.
- Graph **có hướng** và giữ nguyên chiều one-way từ OSM.

**Vì sao chọn cách này:**

- Đề bài nói "construct a map of at least 100 POI", nên để graph là tập POI là cách hiểu sát chữ nhất.
- Khoảng cách và hướng đi đều là thật, không phải đường nối thẳng giữa hai điểm.
- Vẫn có bản đồ đẹp và route bám theo đường.

**Rủi ro:** graph chỉ vài trăm node thì A\* và Dijkstra chênh nhau không nhiều. Cách giảm:

- Nhắm khoảng 150 node, degree trung bình 3–4.
- Chạy experiment trên hơn 100 cặp A/B và báo cáo số trung bình, không dựa vào một cặp.
- Full road network **không** nằm trong scope (nhóm đã quyết định). Graph chỉ gồm các POI.

## 2. Thuật toán dựng edge

Hàm `build_graph(pois, osm_graph, k)` trong `src/graph/builder.py`:

1. **Snap** từng POI vào node OSM gần nhất.
2. Với mỗi POI, tìm **đường ngắn nhất trên mạng OSM** tới $k$ POI gần nhất ($k \approx 6$–$8$, mặc định 6).
3. **Chỉ giữ edge** nếu đường đó không đi xuyên qua POI khác. Như vậy tránh được edge dài thừa, vì đoạn
   A→C đi qua B thì đã được biểu diễn bằng A→B→C.
4. Áp hướng **one-way**, kiểm tra graph **liên thông mạnh**, xử lý các node bị cô lập.
5. Kiểm tra $\text{length}(u, v) \ge \text{haversine}(u, v)$ cho mọi edge. Đây là điều kiện cần để
   heuristic admissible (xem [heuristic_proof.md](heuristic_proof.md)).

> TODO(P2): ghi lại $k$ đã chọn, số edge bị lọc ở bước 3, và cách xử lý từng node cô lập.

## 3. Cấu trúc dữ liệu

`RoadSegment` trong `src/models.py`:

| Trường | Kiểu | Ý nghĩa |
| --- | --- | --- |
| `id` | str | Ví dụ `P001->P017` |
| `source`, `target` | str | ID của POI |
| `length_m` | float | Chiều dài đường thật (mét) |
| `road_type` | str | Tag `highway` của OSM: `primary`, `secondary`, `tertiary`, `residential`… |
| `district` | str | Quận, dùng để áp hệ số traffic |
| `name` | str | Tên đường |
| `lanes` | int | Số làn, dùng để tính capacity |
| `geometry` | tuple[(lat, lon)] | Polyline thật để vẽ bản đồ |

> Proposal có liệt kê thêm `speed_limit` và `oneway`. Trong code, tốc độ tự do lấy theo `road_type` từ
> `configs/default.toml`, còn one-way được thể hiện bằng việc **chỉ tạo edge theo chiều đi được**.
> Nếu cần tốc độ giới hạn thật từ OSM (`maxspeed`) thì mở PR sửa `models.py`.

Class `Graph` trong `src/graph/graph.py`:

| Hàm | Trả về |
| --- | --- |
| `get_neighbors(node_id)` | Danh sách `RoadSegment` đi ra từ node |
| `get_node(node_id)` | `POI` |
| `get_edge(edge_id)` | `RoadSegment` |
| `nodes()`, `edges()` | Toàn bộ node và edge |

`MockGraph` trong `src/mocks.py` có **cùng interface**, để các WP khác code trước khi có graph thật.

## 4. Cache ra file

Graph được lưu vào `data/processed/graph.json` (commit vào git) để chạy không cần internet và không cần
cài `osmnx`.

```json
{
  "version": 1,
  "nodes": [{"id": "P001", "name": "...", "lat": 10.77, "lon": 106.70, "district": "Quan 1", "kind": "intersection"}],
  "edges": [{"id": "P001->P017", "source": "P001", "target": "P017", "length_m": 412.5,
             "road_type": "secondary", "district": "Quan 1", "name": "Lê Lợi", "lanes": 2,
             "geometry": [[10.77, 106.70], [10.771, 106.702]]}]
}
```

> TODO(P2): chốt schema trên với P5 và P6 trước khi commit bản đầu tiên.

Đọc graph: `from src.graph.io import load_default_graph`.

## 5. Kiểm tra (`src/graph/checks.py`)

| Kiểm tra | Hàm | Yêu cầu |
| --- | --- | --- |
| Liên thông mạnh | `check_strongly_connected` | Mọi POI đi tới được mọi POI khác |
| Node cô lập | `check_isolated_nodes` | Không có node nào không có edge vào hoặc ra |
| Độ dài hợp lệ | `check_length_vs_haversine` | $\text{length}(u,v) \ge \text{haversine}(u,v)$ với mọi edge |

## 6. Thống kê graph

> TODO(P2): điền sau khi build.
>
> | Chỉ số | Giá trị |
> | --- | --- |
> | Số node | |
> | Số edge | |
> | Degree trung bình (ra / vào) | |
> | Số edge one-way | |
> | Chiều dài edge (min / trung vị / max) | |
> | Tỉ lệ length / haversine trung bình | |

Kèm hình graph vẽ trên bản đồ (`outputs/graph_preview.html`).
