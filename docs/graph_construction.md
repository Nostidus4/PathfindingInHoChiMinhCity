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

1. **Snap** từng POI vào node OSM gần nhất thuộc **thành phần liên thông mạnh lớn nhất** của mạng OSM
   (node ngoài thành phần này là đường cụt một chiều hoặc đường bị cắt ở biên vùng tải, không thể nối hai
   chiều). Khoảng cách snap được cộng vào `length_m` nên vẫn bảo đảm bước 5.
2. Với mỗi POI, tìm **đường ngắn nhất trên mạng OSM** tới $k$ POI gần nhất (proposal gợi ý $k \approx 6$–$8$; chọn $k = 4$, xem bên dưới).
3. **Chỉ giữ edge** nếu đường đó không đi xuyên qua POI khác. Như vậy tránh được edge dài thừa, vì đoạn
   A→C đi qua B thì đã được biểu diễn bằng A→B→C.
4. Áp hướng **one-way**, kiểm tra graph **liên thông mạnh**, xử lý các node bị cô lập.
5. Kiểm tra $\text{length}(u, v) \ge \text{haversine}(u, v)$ cho mọi edge. Đây là điều kiện cần để
   heuristic admissible (xem [heuristic_proof.md](heuristic_proof.md)).

**Kết quả với dữ liệu thật** (150 POI gồm 130 ngã tư + 20 landmark; mạng OSM 20 233 node / 46 743 cạnh):

| $k$ | Cặp ứng viên | Chiều bị lọc (xuyên POI) | Số cạnh | Degree trung bình | Sửa liên thông |
| --- | --- | --- | --- | --- | --- |
| 3 | 268 | 57 | 479 | 3,19 | không cần |
| **4** | **351** | **94** | **608** | **4,05** | **không cần** |
| 5 | 435 | 156 | 714 | 4,76 | không cần |

- **Chọn $k = 4$:** degree trung bình ≈ 4, ở cận trên mục tiêu 3–4 của proposal, và có nhiều đường thay thế
  hơn $k = 3$, cần cho tiêu chí "đổi giờ xuất phát làm đổi route".
- Không chiều nào thiếu đường đi, không POI nào phải snap (mọi POI nằm đúng trên node thuộc thành phần
  liên thông mạnh của mạng OSM, xem `docs/data_sources.md` §5). Quy tắc snap ở bước 1 vẫn giữ để an toàn
  khi dữ liệu POI thay đổi.
- Cạnh dài nhất (2,8–3,5 km) là các đường vòng thật do đường một chiều và cầu: bán đảo Thanh Đa, cầu Bình
  Triệu, cầu vượt Hàng Xanh.

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

### Schema v1

Các WP khác **không cần đọc JSON trực tiếp**: luôn dùng `load_default_graph()` để nhận `Graph`
(xem mục 7.2). Schema dưới đây chỉ để tham khảo hoặc khi cần đọc file bằng công cụ khác.

Gốc file:

| Khoá | Kiểu | Ý nghĩa |
| --- | --- | --- |
| `version` | int | Phiên bản schema, hiện là `1`. `load_graph` từ chối file khác version |
| `nodes` | list | Danh sách POI, sắp theo `id` |
| `edges` | list | Danh sách cạnh có hướng, sắp theo `id` |

Mỗi phần tử `nodes` (khớp dataclass `POI`):

| Khoá | Kiểu | Đơn vị / giá trị |
| --- | --- | --- |
| `id` | str | Duy nhất; ngã tư dùng id node OSM (`2493366320`), landmark dạng `Lw39514795` |
| `name` | str | Tên POI (UTF-8, giữ dấu tiếng Việt) |
| `lat`, `lon` | float | Độ (WGS84), làm tròn 7 chữ số thập phân |
| `district` | str | `Quan 1`, `Quan 3`, `Quan 5`, `Phu Nhuan`, `Binh Thanh` |
| `kind` | str | `landmark`, `intersection` hoặc `junction` |

Mỗi phần tử `edges` (khớp dataclass `RoadSegment`):

| Khoá | Kiểu | Đơn vị / giá trị |
| --- | --- | --- |
| `id` | str | `"<source>-><target>"`, duy nhất |
| `source`, `target` | str | `id` của POI, phải có trong `nodes` |
| `length_m` | float | Mét, làm tròn 2 chữ số, luôn ≥ haversine(source, target) |
| `road_type` | str | `primary`, `secondary`, `tertiary`, `residential` hoặc `default` |
| `district` | str | Quận của POI `source` |
| `name` | str | Tên đường, có thể rỗng |
| `lanes` | int | ≥ 1 |
| `geometry` | list `[lat, lon]` | Polyline, điểm đầu = POI `source`, điểm cuối = POI `target`; có thể rỗng |

Quy ước file: UTF-8 (`ensure_ascii=False`), node và cạnh sắp theo `id` để diff git gọn. Không có
trường `oneway`: cạnh one-way là cạnh không có cạnh ngược `"<target>-><source>"`.

**Đổi schema:** thêm/bớt trường hoặc đổi ý nghĩa phải tăng `version`, sửa `src/graph/io.py` và
cập nhật bảng trên trong cùng một PR. Thêm trường vào `RoadSegment`/`POI` thì phải sửa
`src/models.py` (file hợp đồng chung, cần PR có owner review).

Đọc graph: `from src.graph.io import load_default_graph`.

## 5. Kiểm tra (`src/graph/checks.py`)

| Kiểm tra | Hàm | Yêu cầu |
| --- | --- | --- |
| Liên thông mạnh | `check_strongly_connected` | Mọi POI đi tới được mọi POI khác |
| Node cô lập | `check_isolated_nodes` | Không có node nào không có edge vào hoặc ra |
| Độ dài hợp lệ | `check_length_vs_haversine` | $\text{length}(u,v) \ge \text{haversine}(u,v)$ với mọi edge |

## 6. Thống kê graph

Build ngày 08/10/2026, $k = 4$, từ `pois.csv` hiện tại:

| Chỉ số | Giá trị |
| --- | --- |
| Số node | 150 (30 mỗi quận, gồm 4 landmark mỗi quận) |
| Số edge | 608 |
| Degree trung bình (ra / vào) | 4,05 |
| Số edge one-way | 70 |
| Chiều dài edge (min / trung vị / max) | 246 / 676 / 3 477 m |
| Tỉ lệ length / haversine trung bình | 1,55 |

Kiểm tra liên quan WP3/WP4 trên graph thật: `SyntheticProvider` + `compute_speed_bounds` chạy 0,26 s,
`check_fifo` trên lưới 15 phút không có vi phạm.

Kèm hình graph vẽ trên bản đồ (`outputs/graph_preview.html`).

## 7. Input / Output và cách dùng (cho các WP khác)

> Mục này để các WP khác tự tra cứu khi làm phần liên quan tới graph.

### 7.1 Input (WP2 cần gì)

| Input | Từ | Hàm / file | Yêu cầu |
| --- | --- | --- | --- |
| Danh sách POI | P1 | `src.data.poi_io.load_pois()` → `data/processed/pois.csv` | `list[POI]`, id không trùng; `district` đúng **y hệt** key trong `configs/default.toml`: `"Quan 1"`, `"Quan 3"`, `"Quan 5"`, `"Phu Nhuan"`, `"Binh Thanh"` (không dấu) |
| Mạng đường OSM | P1 | `src.data.osm_fetch.fetch_road_network()` hoặc file `.graphml` (`--osm`) | `networkx.MultiDiGraph` của osmnx (`network_type="drive"`): node có `x` (lon), `y` (lat); cạnh có `length` (m), `highway`, `name`, `lanes`, `geometry` (nếu có) |

Khi build, script báo lại cho P1 các trường hợp cần xem lại: hai POI snap vào cùng một node OSM (gần như
trùng), POI cách node đường gần nhất hơn 100 m, POI không nối được để graph liên thông mạnh.

### 7.2 Output (WP2 cung cấp gì)

File `data/processed/graph.json` (commit vào git, schema ở mục 4), đọc bằng:

```python
from src.graph.io import load_default_graph

graph = load_default_graph()  # -> Graph
graph.nodes()  # list[POI]
graph.edges()  # list[RoadSegment]
graph.get_node("P001")  # POI (KeyError nếu id không tồn tại)
graph.get_edge("P001->P017")  # RoadSegment (KeyError nếu không tồn tại)
graph.get_neighbors("P001")  # list[RoadSegment] đi ra (list mới mỗi lần gọi)
```

Chưa có `graph.json` thì dùng `MockGraph` trong `src/mocks.py` (cùng interface). Chỉ dùng 5 hàm ở trên;
`Graph` có thêm `get_in_edges`, `in`, `len` nhưng `MockGraph` không có, dùng sẽ hỏng test trên mock.

**Cam kết của graph thật** (kiểm bằng `src/graph/checks.py`, script không ghi file nếu có lỗi):

- Liên thông mạnh: mọi POI đi tới được mọi POI. Không có node cô lập.
- Mọi cạnh có `length_m ≥ haversine(source, target)` (sai số 1 m).
- ≥ 100 node, ≥ 20 node mỗi quận.

**Quy ước dữ liệu:**

| Trường | Quy ước |
| --- | --- |
| `RoadSegment.id` | `"<source>-><target>"`. Chiều ngược chỉ tồn tại nếu đường đi được hai chiều (không có cạnh ngược = one-way) |
| `length_m` | Chiều dài đường OSM + khoảng cách snap ở hai đầu (mét), nên luôn ≥ haversine |
| `road_type` | Chỉ một trong `primary`, `secondary`, `tertiary`, `residential`, `default` (khớp `[greenshields.free_flow_kmh]`) |
| `lanes` | int ≥ 1; OSM không có dữ liệu thì mặc định 1 |
| `district` | Quận của POI đầu cạnh (`source`), cùng chuỗi với config |
| `name` | Tên đường chiếm phần lớn chiều dài cạnh; có thể rỗng |
| `geometry` | Tuple các điểm **(lat, lon)**; điểm đầu là POI `source`, điểm cuối là POI `target`. Trong `MockGraph` thì rỗng |

### 7.3 Ghi chú cho từng WP

| WP | Cần biết |
| --- | --- |
| P1 (WP1) | Xem 7.1. Thay POI bị báo lỗi nhưng vẫn giữ ≥ 20 POI mỗi quận |
| P3 (WP3) | Dùng `road_type`, `lanes`, `district` của cạnh cho profile và capacity. 150 node, 608 cạnh |
| P4 (WP4) | Chứng minh admissibility dựa vào `length_m ≥ haversine`: đường OSM + hai đoạn snap không thể ngắn hơn đường thẳng (bất đẳng thức tam giác) |
| P5 (WP5) | Graph thật liên thông mạnh nên không có ca no-path; test no-path dùng `MockGraph` (`A→G`). Kiểm id hợp lệ bằng `{p.id for p in graph.nodes()}` hoặc bắt `KeyError`, rồi đổi thành `ValueError` trong `Pathfinder` |
| P6 (WP6) | Vẽ route bằng `edge.geometry`, tên đường `edge.name` (rỗng thì hiện `road_type`). POI có `name`, `district`, `kind` cho `list-pois`. Folium bản hiện tại cần API key cho tiles `cartodbpositron`, nên dùng tiles mặc định |

### 7.4 Dựng lại graph

```bash
uv sync --group data
uv run python scripts/build_graph.py --preview                  # k = 4, dùng pois.csv + cache OSM của P1
uv run python scripts/build_graph.py --osm data/raw/hcmc_drive.graphml --out /tmp/graph.json
```

Script in thống kê (dùng cho mục 6), các lần sửa liên thông và cảnh báo; `--preview` xuất
`outputs/graph_preview.html` (cạnh one-way màu đỏ). Có lỗi kiểm tra thì thoát mã 1 và không ghi file.
