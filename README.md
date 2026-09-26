# hcmc-pathfinding

**Time-Dependent Traffic-Aware A\*** cho *TOPIC 2: Pathfinding in Ho Chi Minh City*.
Nhóm 6 người · Python 3.12 · quản lý bằng [uv](https://docs.astral.sh/uv/).

Bài toán: tìm đường giữa hai POI (ngã tư hoặc landmark) trong 5 quận cũ của TP.HCM
(Quận 1, 3, 5, Bình Thạnh, Phú Nhuận). Chi phí mỗi đoạn đường là **thời gian đi**, và thời gian
này thay đổi theo **giờ xuất phát** vì giao thông được mô phỏng bằng mô hình Greenshields
có giờ cao điểm. Nhóm so sánh 4 heuristic: `zero`, `static_vmax`, `dynamic_ub`,
`dynamic_weighted`.

---

## 1. Bắt đầu nhanh

```bash
# 1. Cài uv (nếu chưa có)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone và cài môi trường (uv tự tải Python 3.12)
git clone https://github.com/Nostidus4/PathfindingInHoChiMinhCity.git && cd PathfindingInHoChiMinhCity
uv sync

# 3. Kiểm tra mọi thứ chạy được
uv run ruff check
uv run pytest
```

Một số người cần cài thêm group riêng:

| Lệnh | Ai cần | Cài thêm |
|---|---|---|
| `uv sync` | Tất cả | numpy, pandas, matplotlib, folium, pytest, ruff |
| `uv sync --group data` | P1, P2 | osmnx, geopandas, shapely (nặng, dễ lỗi khi cài) |
| `uv sync --group ui` | P6 | streamlit, streamlit-folium |

> Những người không cài group `data` sẽ dùng `data/processed/pois.csv` và
> `data/processed/graph.json` do P1, P2 tạo và commit sẵn vào git.

## 2. Cách chạy

```bash
# Tìm đường
uv run hcmc route --start <POI_ID> --goal <POI_ID> --time 08:00 --heuristic dynamic_ub --trace

# So sánh 4 heuristic trên cùng một cặp điểm
uv run hcmc compare --start <POI_ID> --goal <POI_ID> --time 17:30

# Kiểm tra admissibility / consistency / FIFO
uv run hcmc validate

# Chạy thí nghiệm, xuất CSV và biểu đồ vào outputs/
uv run hcmc experiments

# Liệt kê POI
uv run hcmc list-pois --district "Quan 1"

# Tạo dữ liệu (P1, P2, cần group data)
uv run python scripts/build_pois.py
uv run python scripts/build_graph.py

# Giao diện web (P6, cần group ui)
uv run streamlit run app/streamlit_app.py
```

## 3. Cấu trúc thư mục

```
hcmc-pathfinding/
├── pyproject.toml, uv.lock, .python-version   cấu hình project + khoá phiên bản
├── .github/workflows/ci.yml                   CI: uv sync + ruff + pytest
├── configs/default.toml                       tham số mô phỏng, heuristic, seed
├── data/
│   ├── raw/          cache OSM (không commit)
│   ├── processed/    pois.csv, graph.json (commit)
│   └── snapshots/    dữ liệu real-time đóng băng (nếu có)
├── scripts/          build_pois.py, build_graph.py, survey_realtime.py
├── src/              toàn bộ source code (import bằng `from src... import ...`)
├── app/              streamlit_app.py (T2, extra)
├── tests/            test cho từng WP
├── docs/             tài liệu thuật toán, mô hình, báo cáo
└── outputs/          bản đồ, bảng, hình sinh ra (không commit)
```

### Bên trong `src/`

| Thư mục / file | WP | Owner | Nhiệm vụ |
|---|---|---|---|
| `models.py` | nền tảng | P6 + P5 | Hợp đồng chung: `POI`, `RoadSegment`, `TrafficState`, `RouteResult`, Protocol `TrafficProvider`, `Heuristic` |
| `geo.py` | nền tảng | P6 + P5 | `haversine_m`, viết bằng Python thuần |
| `timeutil.py` | nền tảng | P6 + P5 | Thời điểm tính bằng giây từ 00:00, `parse_hhmm`, `GRID_STEP = 900` |
| `config.py` | nền tảng | P6 + P5 | `SimConfig.load()` đọc `configs/default.toml` |
| `mocks.py` | nền tảng | P6 + P5 | Graph giả 7 node có đáp án biết trước, cùng `MockTrafficProvider` |
| `data/` | WP1 | P1 | Lấy dữ liệu OSM, chọn POI, gán quận, kiểm tra, xem trước trên bản đồ |
| `graph/` | WP2 | P2 | Class `Graph`, dựng đồ thị từ POI, đọc/ghi `graph.json`, kiểm tra liên thông |
| `traffic/` | WP3 | P3 | Greenshields, profile giờ cao điểm, `SyntheticProvider`, `SpeedBounds` |
| `cost/` | WP4 | P4 | `speed_model`, `edge_cost`, và 4 heuristic trong `cost/heuristics/` |
| `search/` | WP5 | P5 | `astar`, `dijkstra`, `trace`, facade `Pathfinder` |
| `validation/` | WP5 | P5 (`fifo.py`: P3) | Kiểm admissibility, consistency, tìm counterexample, kiểm FIFO |
| `experiments/` | WP6 | P6 | Sinh kịch bản, chạy thí nghiệm, demo phụ thuộc thời gian, vẽ biểu đồ |
| `viz/` | WP6 | P6 | `render_map` bằng folium, xuất HTML (T1) |
| `cli.py` | WP6 | P6 | Lệnh `hcmc` (T0) |

Đầu mỗi file có docstring ghi rõ nhiệm vụ, owner và các ràng buộc. **Đọc docstring trước khi code.**

## 4. Luồng dữ liệu

```
OSM ──► data/ ──► pois.csv ──► graph/ ──► graph.json
                                             │
               configs/default.toml ──► traffic/ (TrafficProvider, SpeedBounds)
                                             │
                                          cost/ (edge_cost, heuristic)
                                             │
                                          search/ (astar ◄── Pathfinder)
                                             │
                     validation/ · experiments/ · viz/ · cli.py · app/
```

Mọi thứ ở tầng trên (CLI, UI, experiments) **chỉ gọi `Pathfinder`**:

```python
from src.config import SimConfig
from src.graph.io import load_default_graph
from src.search.pathfinder import Pathfinder
from src.timeutil import parse_hhmm
from src.traffic.synthetic import SyntheticProvider

cfg = SimConfig.load()
graph = load_default_graph()
pf = Pathfinder(graph, SyntheticProvider(graph, cfg, seed=cfg.seed), cfg)
result = pf.route("A", "B", parse_hhmm("08:00"), heuristic_mode="dynamic_ub")
```

## 5. Quy ước bắt buộc

- **Quy tắc phụ thuộc:** mỗi tầng chỉ import tầng bên dưới nó.
  `models/geo/timeutil/config → data → graph → traffic → cost → search → validation → experiments/viz/cli/app`.
  `search/` **không được** import `viz`, `cli`, `osmnx` hay `streamlit`, để A\* không phụ thuộc UI/API.
- **Đơn vị chốt một lần:**
  - `TrafficState`: tốc độ km/h, mật độ veh/km, lưu lượng veh/h
  - Thời gian: giây. Thời điểm tính bằng giây kể từ 00:00.
  - Chiều dài: mét
  - **Chỉ `cost/speed_model.py` được đổi đơn vị.**
- **Heuristic là object:** tạo một lần bằng `make_heuristic(mode, graph, bounds, params)`,
  sau đó gọi `h(node, goal, t)` và nhận về số giây. Không gọi provider bên trong heuristic.
- **`astar()` nhận `edge_cost` và `heuristic` dưới dạng hàm.** Chữ ký dễ dùng hơn nằm ở `Pathfinder.route(...)`.
- **Không hard-code tham số:** mọi con số mô phỏng đặt trong `configs/default.toml`.
- **osmnx và geopandas chỉ import bên trong hàm** để người không cài group `data` vẫn import được package.

## 6. Quy trình làm việc nhóm

1. **Ngày đầu:** cả nhóm đọc `src/models.py` và góp ý trong PR. Khi hết ý kiến thì gắn tag
   `interfaces-v1` và **đóng băng**. Sau đó muốn đổi `models.py` thì phải mở PR và có đủ owner review.
2. **Làm song song trên mock:** chưa có dữ liệu thật thì dùng `src/mocks.py`
   (`MockGraph`, `MockTrafficProvider`, `MOCK_OPTIMA`). Fixture có sẵn trong `tests/conftest.py`.
3. **Mỗi người chỉ sửa file trong subpackage của mình.** Muốn sửa file của người khác thì mở PR.
4. **Review theo cặp:** P1 ↔ P2 · P3 ↔ P4 · P5 ↔ P6.
5. **`main` luôn xanh:** trước khi merge phải qua cả hai lệnh

   ```bash
   uv run ruff check && uv run ruff format --check && uv run pytest
   ```

   CI trên GitHub chạy lại đúng các lệnh này cho mỗi PR.

Gợi ý đặt tên branch: `wp3/greenshields`, `wp5/astar`, `fix/cli-no-path`.

## 7. Test

| File test | Owner | Kiểm tra gì |
|---|---|---|
| `test_foundation.py` | P6 + P5 | geo, timeutil, config, mocks (đã chạy được) |
| `test_poi_data.py` | P1 | ≥ 100 POI, ≥ 20 POI mỗi quận, không trùng, không nằm ngoài ranh giới |
| `test_graph.py` | P2 | Liên thông mạnh, không có node cô lập, `length ≥ haversine` |
| `test_greenshields.py`, `test_synthetic_provider.py`, `test_speed_bounds.py`, `test_fifo.py` | P3 | `q = k·v`, tái lập được với seed, `v_ub` không tăng, FIFO |
| `test_speed_model.py`, `test_edge_cost.py`, `test_heuristics.py` | P4 | Đổi đơn vị đúng, cost tính bằng giây, đủ 4 mode |
| `test_astar.py`, `test_admissibility.py`, `test_consistency.py`, `test_counterexamples.py` | P5 | Đúng đáp án mock, mode `zero` ra cùng kết quả với Dijkstra |
| `test_time_dependence.py` | P5 / P6 | Cost giờ cao điểm lớn hơn giờ thấp điểm |
| `test_cli.py` | P6 | Input sai, trường hợp không có đường |

Các test chưa viết đang được đánh dấu `skip`. Khi cài xong module, hãy xoá dòng
`pytestmark = pytest.mark.skip(...)` rồi viết test thật.

```bash
uv run pytest                          # chạy tất cả
uv run pytest tests/test_astar.py -v   # chạy một file
uv run pytest --cov=src                # xem coverage
```

## 8. Trạng thái hiện tại

- [x] Skeleton, CI, config, tầng nền tảng (`models`, `geo`, `timeutil`, `config`, `mocks`)
- [ ] WP1: POI (P1)
- [ ] WP2: Graph (P2)
- [ ] WP3: Traffic (P3)
- [ ] WP4: Cost + heuristics (P4)
- [ ] WP5: Search + validation (P5)
- [ ] WP6: Experiments, viz, CLI (P6)
- [ ] T2: Streamlit app (extra)

Các hàm chưa cài đặt đều `raise NotImplementedError("TODO(Px)")`, trong đó `Px` là người phụ trách.

## 9. Tài liệu

| File | Owner | Nội dung |
|---|---|---|
| `docs/scope.md` | Toàn nhóm | Đề bài, yêu cầu R1–R6, quyết định thiết kế, phạm vi, rủi ro, tiêu chí hoàn thành |
| `docs/data_sources.md` | P1 | Nguồn OSM, license, kết quả khảo sát dữ liệu real-time |
| `docs/graph_construction.md` | P2 | Cách dựng graph POI, định dạng graph.json, các kiểm tra |
| `docs/traffic_model.md` | P3 | Mô hình Greenshields, profile giờ cao điểm, SpeedBounds |
| `docs/heuristic_proof.md` | P4 | Chứng minh admissible và consistent |
| `docs/algorithm_walkthrough.md` | P5 | Giải thích A\* từng bước, sinh từ `--trace` |
| `docs/report/` | P6 | Báo cáo tổng hợp |

## 10. Lỗi thường gặp

- **Cài `osmnx` hoặc `geopandas` bị lỗi:** chỉ P1 và P2 cần hai thư viện này. Người khác chạy `uv sync` là đủ.
- **`ModuleNotFoundError: src`:** chạy lệnh qua `uv run ...` từ thư mục gốc repo, hoặc chạy lại `uv sync`.
- **`NotImplementedError: TODO(Px)`:** phần đó chưa có ai cài đặt. Dùng mock hoặc hỏi người phụ trách.

Dữ liệu bản đồ © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright), license ODbL.
