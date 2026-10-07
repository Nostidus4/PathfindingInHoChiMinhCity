# Hướng dẫn test toàn bộ project

> Owner: **P6** (tích hợp) · Review: P5 · Áp dụng cho mọi WP

Tài liệu này mô tả cách kiểm tra cả project theo **hai hướng**:

| Hướng | Dữ liệu | Khi nào dùng | Điều kiện |
| --- | --- | --- | --- |
| **A — Mock** | `src/mocks.py` (7 node, đáp án biết trước) | Hằng ngày, trước mỗi PR, trên CI | Chỉ cần `uv sync` |
| **B — Real data** | `data/processed/pois.csv` + `graph.json` | Trước khi chốt số liệu báo cáo | Cần `graph.json` (WP2) + `uv sync --group data` |

Hướng A **luôn chạy được** và là cổng bắt buộc để merge. Hướng B cho ra số liệu thật đưa vào báo cáo.
Mọi con số kỳ vọng trong tài liệu này tái lập được bằng `seed` trong [`configs/default.toml`](../configs/default.toml).

---

## 0. Chuẩn bị môi trường

```bash
uv sync                  # Tất cả: numpy, pandas, matplotlib, folium, pytest, ruff
uv sync --group data     # Hướng B: osmnx, geopandas, shapely, networkx
uv sync --group ui       # T2 Streamlit (chưa cài đặt): streamlit, streamlit-folium
```

### Hai lưu ý về môi trường Windows

**1. Nếu `uv run hcmc` báo lỗi `Application Control policy has blocked this file`**, dùng dạng module tương
đương — mọi lệnh trong tài liệu này đều có thể thay thế như sau:

```bash
uv run hcmc route ...              # dạng chuẩn (README)
uv run python -m src.cli route ... # dạng thay thế, luôn chạy được
```

**2. Tiếng Việt trong output.** PowerShell hiển thị đúng. Nếu dùng Git Bash / cmd và thấy lỗi
`'charmap' codec can't encode`, chạy trước:

```bash
export PYTHONIOENCODING=utf-8     # Git Bash
chcp 65001                        # cmd
```

Đây là lỗi hiển thị của terminal, không phải lỗi code — file ghi ra `outputs/` luôn là UTF-8 hợp lệ.

---

## 1. Năm lớp kiểm tra

| Lớp | Nội dung | Lệnh | Hướng A | Hướng B |
| --- | --- | --- | :-: | :-: |
| L1 | Lint + format | `ruff check`, `ruff format --check` | ✅ | ✅ |
| L2 | Unit + integration test | `pytest` | ✅ | ✅ |
| L3 | Smoke CLI thủ công | `hcmc route/compare/list-pois` | ✅ | ✅ |
| L4 | Kiểm chứng thuật toán | `hcmc validate` | ✅ | ✅ |
| L5 | Thí nghiệm, sinh số liệu báo cáo | `hcmc experiments` | ✅ | ✅ |

CI ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)) chỉ chạy **L1 + L2 ở hướng A**
(`uv sync --locked` không cài group `data`). L3–L5 và hướng B phải chạy tay.

---

# HƯỚNG A — Test trên mock

## A1. Cổng bắt buộc trước mỗi PR

```bash
uv run ruff check && uv run ruff format --check && uv run pytest
```

Kết quả kỳ vọng:

```
All checks passed!
210 passed, 7 skipped
```

> **Lưu ý về `ruff format --check`:** hiện có **2 file fail từ trước**, không thuộc WP nào đang sửa:
> `scripts/build_pois.py` và `docs/graph_construction.md`. CI không chạy lệnh này nên `main` vẫn xanh.
> Khi nào P1/P2 chạm vào hai file đó thì sửa luôn.

### 7 test đang skip — đều có lý do hợp lệ

| Số | File | Lý do | Hết skip khi nào |
| --: | --- | --- | --- |
| 4 | `test_graph.py` (builder) | thiếu `networkx` | `uv sync --group data` |
| 2 | `test_graph.py` (graph thật) | thiếu `data/processed/graph.json` | P2 commit `graph.json` |
| 1 | `test_poi_data.py` | `TODO(P1)`: **test chưa được viết** | P1 viết test |

Xem lại danh sách bất cứ lúc nào:

```bash
uv run pytest -q -rs        # -rs = in lý do skip
```

## A2. Test theo từng work package

Khi chỉ sửa một WP, chạy đúng phần của mình cho nhanh:

| WP | Người | Lệnh | Số test |
| --- | --- | --- | --: |
| Nền tảng | P6+P5 | `uv run pytest tests/test_foundation.py` | 6 |
| WP1 POI | P1 | `uv run pytest tests/test_poi_data.py` | 1 *(skip)* |
| WP2 Graph | P2 | `uv run pytest tests/test_graph.py` | 31 |
| WP3 Traffic | P3 | `uv run pytest tests/test_greenshields.py tests/test_synthetic_provider.py tests/test_speed_bounds.py tests/test_fifo.py tests/test_traffic_profiles.py tests/test_timeslots.py` | 69 |
| WP4 Cost + heuristic | P4 | `uv run pytest tests/test_speed_model.py tests/test_edge_cost.py tests/test_heuristics.py` | 30 |
| WP5 Search + validation | P5 | `uv run pytest tests/test_astar.py tests/test_admissibility.py tests/test_consistency.py tests/test_counterexamples.py` | 48 |
| WP6 CLI/viz/experiments | P6 | `uv run pytest tests/test_cli.py tests/test_experiments.py tests/test_viz.py` | 29 |
| WP5 ↔ WP6 | P5/P6 | `uv run pytest tests/test_time_dependence.py` | 3 |

Lọc theo tên test:

```bash
uv run pytest -k "admissib or consistency" -v
uv run pytest tests/test_astar.py::test_zero_mode_matches_independent_dijkstra -v
uv run pytest -x -q                    # dừng ở lỗi đầu tiên
uv run pytest --lf                     # chỉ chạy lại các test đã fail
```

## A3. Coverage

```bash
uv run pytest --cov=src --cov-report=term-missing
uv run pytest --cov=src --cov-report=html && start htmlcov/index.html
```

Mức hiện tại: **`src/` 79%**. Hai subpackage lõi thuật toán phải giữ ở mức cao:

| Module | Coverage |
| --- | --: |
| `src/search/` | 96–100% |
| `src/validation/` | 97–100% |

Phần coverage thấp còn lại tập trung ở `src/data/` (cần group `data`) và các nhánh lỗi của `cli.py`.

## A4. Smoke test CLI trên mock

Graph mock 7 node A–G (xem `src/mocks.py`), tốc độ hằng 36 km/h, `A → G` **không có đường**
(G chỉ có cạnh một chiều G→A).

Chạy từng lệnh và đối chiếu:

```bash
# 1. Liệt kê POI
uv run hcmc list-pois --mock
uv run hcmc list-pois --mock --district "Quan 3"       # => Tổng: 3 POI

# 2. Tìm đường (happy path)
uv run hcmc route --mock --start A --goal F --time 08:00 --heuristic dynamic_ub

# 3. Trace từng bước A*
uv run hcmc route --mock --start C --goal D --time 17:30 --heuristic dynamic_ub --trace

# 4. Xuất bản đồ HTML
uv run hcmc route --mock --start A --goal F --map --out outputs/route.html

# 5. So sánh 4 heuristic
uv run hcmc compare --mock --start C --goal D --time 17:30

# 6. Kiểm chứng admissibility / consistency / FIFO
uv run hcmc validate --mock

# 7. Thí nghiệm
uv run hcmc experiments --mock --n 20 --out-dir outputs
```

### Bảng exit code kỳ vọng

Đây là phần L3 quan trọng nhất: CLI phải xử lý input sai **không văng traceback**.

| Lệnh | Exit | Thông báo kỳ vọng |
| --- | :-: | --- |
| `route --mock --start A --goal F` | `0` | In route |
| `route --mock --start A --goal G` | `1` | `Không có đường từ A (Mock A) tới G (Mock G)` |
| `route --mock --start A --goal ZZZ` | `1` | `POI 'ZZZ' không tồn tại` |
| `route --mock --start A --goal F --time 25:00` | `1` | `Thời gian ngoài khoảng` |
| `route --mock --start A --goal F --heuristic magic` | `2` | argparse: `invalid choice` |
| `list-pois` *(không có `--mock`, chưa có graph.json)* | `1` | `Không tìm thấy ... graph.json` + gợi ý `--mock` |
| `compare --mock --start A --goal G` | `1` | `Không có đường` |
| `validate --mock` | `0` | 8 dòng `[ĐẠT]` |
| `experiments --mock --n 20` | `0` | Bảng summary + 7 file |

Kiểm tất cả trong một lần (PowerShell):

```powershell
$cases = @(
  @{a=@("route","--mock","--start","A","--goal","F");            exp=0},
  @{a=@("route","--mock","--start","A","--goal","G");            exp=1},
  @{a=@("route","--mock","--start","A","--goal","ZZZ");          exp=1},
  @{a=@("route","--mock","--start","A","--goal","F","--time","25:00"); exp=1},
  @{a=@("compare","--mock","--start","A","--goal","G");           exp=1},
  @{a=@("validate","--mock");                                     exp=0},
  @{a=@("list-pois","--mock");                                    exp=0}
)
foreach ($c in $cases) {
  uv run python -m src.cli @($c.a) 2>&1 | Out-Null
  $ok = if ($LASTEXITCODE -eq $c.exp) { "OK  " } else { "FAIL" }
  Write-Output "$ok exit=$LASTEXITCODE (ky vong $($c.exp))  $($c.a -join ' ')"
}
```

## A5. Kết quả kỳ vọng của `validate --mock`

```
[ĐẠT] FIFO trên mọi edge: 0 vi phạm
[ĐẠT] zero admissible: 0 vi phạm
[ĐẠT] zero consistent: 0 vi phạm
[ĐẠT] static_vmax admissible: 0 vi phạm
[ĐẠT] static_vmax consistent: 0 vi phạm
[ĐẠT] dynamic_ub admissible: 0 vi phạm
[ĐẠT] dynamic_ub consistent: 0 vi phạm
[ĐẠT] dynamic_weighted có phản ví dụ (cost A* > Dijkstra): 15 vi phạm, ví dụ: {...}
```

**Dòng cuối phải có vi phạm.** `dynamic_weighted` (w = 1.5 > 1) được thiết kế để **không** admissible;
không tìm ra phản ví dụ nghĩa là validator hoặc engine có vấn đề, nên CLI tính đó là **LỖI**.

Và `compare --mock --start C --goal D --time 17:30` phải cho thấy đúng ba điều đề bài hỏi:

```
Mode                Cost (s)       ETA  Expanded  Runtime ms  Ghi chú
zero                   135.2  17:32:15         5        0.10
static_vmax            135.2  17:32:15         3        0.07
dynamic_ub             135.2  17:32:15         3        0.05
dynamic_weighted       151.2  17:32:31         2        0.03   vượt tối ưu 11.77%
```

- 3 mode admissible cho **cùng cost tối ưu** (135.2 s);
- heuristic động cắt expanded nodes **5 → 3** mà vẫn tối ưu;
- heuristic không admissible nhanh nhất (2 node) nhưng **chọn sai đường** (+11.77%).

## A6. Hai hạn chế đã biết của hướng A

Hai điều này **không phải bug**, chỉ là giới hạn của graph 7 node. Đừng mất thời gian debug:

1. **A\* không thắng Dijkstra rõ ràng.** Trung bình 20 kịch bản: `dynamic_ub` expand 3.8 vs `zero` 4.1
   (chênh ~7%). Trên graph 150 node, chênh lệch là **3 vs 15 node (5×)**.
2. **Time-demo chỉ đổi cost, không đổi route.** 37 mốc giờ 05:00–23:00 trên cặp G→F: cost biến thiên
   287 s → 362 s (**+26%**) nhưng route luôn `G > A > B > D > F`, nên `time_demo_map.html` chỉ vẽ 1 tuyến.

Cả hai chỉ hết khi chuyển sang hướng B.

---

# HƯỚNG B — Test trên dữ liệu thật

> **Điều kiện tiên quyết:** `data/processed/graph.json` phải tồn tại. Hiện **chưa được commit** — đây là
> blocker duy nhất còn lại của project.

## B1. Dựng và commit `graph.json` (P2)

```bash
uv sync --group data
uv run python scripts/build_graph.py --k 6 --preview
```

Các bước script chạy: `load_pois → fetch_road_network → build_graph → run_all_checks → save_graph`.

**Cần kiểm trong output:**

| Chỉ số | Kỳ vọng |
| --- | --- |
| Số node | ≥ 100 (dataset có 150 POI) |
| Số node theo quận | mỗi quận ≥ 20 |
| `run_all_checks` | **rỗng** — không có node cô lập, liên thông mạnh, `length ≥ haversine` |
| Tỉ lệ `length / haversine` TB | > 1.0 (đường thật dài hơn đường chim bay) |
| Số edge one-way | > 0 (mạng thật có đường một chiều) |

Mở `outputs/graph_preview.html` để xem POI và cạnh trên bản đồ (cạnh một chiều tô đỏ).

Sau đó **commit file** để cả nhóm và CI dùng được — `.gitignore` không chặn `data/processed/`:

```bash
git add data/processed/graph.json && git commit -m "WP2: commit graph.json"
```

Rồi điền 2 `TODO(P2)` trong [graph_construction.md](graph_construction.md) bằng số thật.

## B2. Kiểm dữ liệu POI và graph độc lập

```bash
uv run python -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter
from src.data.poi_io import load_pois
from src.data.poi_validate import validate_pois
from src.data.districts import assign_district
from src.graph.io import load_default_graph
from src.graph.checks import run_all_checks

pois = load_pois()
print('POI:', len(pois), '| loi validate:', validate_pois(pois))
print('theo quan:', dict(sorted(Counter(p.district for p in pois).items())))
print('district lech polygon:', sum(1 for p in pois if assign_district(p.lat,p.lon) != p.district))

g = load_default_graph()
print('graph:', len(g.nodes()), 'node,', len(g.edges()), 'edge')
print('run_all_checks:', run_all_checks(g) or 'DAT (rong)')
"
```

Trạng thái hiện tại của `pois.csv`: **150 POI, 30/quận, 0 lỗi validate**. Hai điểm cần biết:

- `kind` toàn bộ là `intersection` — chưa có POI loại `landmark`.
- Gán quận dùng **5 hình chữ nhật** ([`districts.py:15`](../src/data/districts.py#L15)), không phải ranh
  giới hành chính thật, nên một số POI bị gán lệch (ví dụ POI trên Trần Não được gán `Binh Thanh`).
  Chỉ ảnh hưởng `district_factor` của traffic, **không** ảnh hưởng tính đúng của A\*.

## B3. Full suite ở hướng B

```bash
uv sync --group data
uv run pytest -q -rs
```

Kết quả kỳ vọng sau khi có `graph.json` **và** group `data`:

```
216 passed, 1 skipped
```

| Thay đổi so với hướng A | Vì sao |
| --- | --- |
| +4 test (builder) | có `networkx` |
| +2 test (`test_real_graph_passes_checks`, `test_real_graph_size`) | có `graph.json` |
| còn 1 skip | `test_poi_data.py` — `TODO(P1)`, test chưa được viết |

Hai test graph thật kiểm đúng tiêu chí R1: `len(nodes) >= 100`, đủ 5 quận, mỗi quận `>= 20`, và
`run_all_checks()` rỗng.

## B4. Smoke test CLI trên dữ liệu thật

Bỏ `--mock` là mọi lệnh tự đọc `graph.json`. POI id là OSM node id (số dài), nên lấy id trước:

```bash
uv run hcmc list-pois --district "Quan 1" | head -5
```

Rồi thay vào (ví dụ dùng hai id lấy được):

```bash
uv run hcmc route --start <ID_A> --goal <ID_B> --time 08:00 --heuristic dynamic_ub --trace --map
uv run hcmc compare --start <ID_A> --goal <ID_B> --time 17:30
```

**Kỳ vọng khác hướng A:** `expanded` của `dynamic_ub` phải **thấp hơn rõ rệt** `zero`. Đo trên graph
150 node / 900 edge: `zero` expand 15 node, `dynamic_ub` và `static_vmax` expand 3 node.

## B5. `validate` trên graph thật — lưu ý thời gian chạy

```bash
uv run hcmc validate
```

Lệnh này **nặng hơn hướng mock rất nhiều**. Số đo trên graph 150 node / 900 edge, cấu hình mặc định
(10 goal lấy mẫu, lưới 15 phút 73 mốc, lưới giờ 19 mốc):

| Bước | Thời gian |
| --- | --: |
| `Pathfinder.__init__` (gồm `compute_speed_bounds`) | 0,3 s |
| `check_fifo` — mọi edge × 73 mốc | 0,2 s |
| `check_admissibility` — **1 mode** (150 node × 10 goal × 19 mốc) | **10,1 s** |
| `check_consistency` — **1 mode** (10 goal × 73 mốc × 900 edge) | **3,6 s** |
| `find_counterexamples` — 120 kịch bản | 0,3 s |
| **Tổng `hcmc validate`** (3 mode admissible + FIFO + phản ví dụ) | **~40–60 s** |

Nếu cần nhanh hơn khi debug, giảm phạm vi quét bằng cách sửa trong [`src/cli.py`](../src/cli.py):
`VALIDATION_GOALS` (mặc định 10) hoặc dùng lưới thưa hơn cho `check_consistency`.

Kỳ vọng: **y như hướng A** — 3 mode admissible 0 vi phạm, `dynamic_weighted` có phản ví dụ. Trên graph cỡ
150 node, `dynamic_weighted` sinh rất nhiều phản ví dụ (đo được 66/120 kịch bản), nên đây là nơi lấy ca
đẹp nhất để vẽ lên bản đồ cho báo cáo.

Sau khi chạy, điền 2 `TODO` trong [heuristic_proof.md](heuristic_proof.md) (§8 kết quả bằng số, và ca phản
ví dụ thật) và 2 `TODO(P3)` trong [traffic_model.md](traffic_model.md) (bảng `fifo_report`).

## B6. Sinh số liệu báo cáo

```bash
uv run hcmc experiments --n 120
```

`--n 120` theo scope §4.1 (≥ 100 cặp A/B). Sinh 7 file vào `outputs/`:

| File | Dùng cho chương báo cáo |
| --- | --- |
| `experiments.csv` | Dữ liệu thô, 120 × 4 mode |
| `summary.md` | Chương 9: bảng so sánh 4 heuristic |
| `expanded_nodes.png`, `runtime.png` | Chương 9: biểu đồ |
| `time_demo.csv`, `cost_vs_time.png` | Chương 9: demo time-dependent |
| `time_demo_map.html` | Chương 9/10: các route chồng nhau |

**Trên dữ liệu thật phải kiểm thêm hai điều mà mock không cho thấy:**

1. `summary.md`: cột `Expanded TB` của `dynamic_ub` phải **nhỏ hơn rõ rệt** `zero`, và cột `Tối ưu (%)`
   của 3 mode admissible phải là `100.0`.
2. `time_demo.csv`: phải có ít nhất một dòng `route_changed = True` — tức đổi giờ xuất phát thì **đổi
   tuyến**, không chỉ đổi cost. Đây là tiêu chí hoàn thành scope §8 ở mức mạnh nhất. Kiểm nhanh:

   ```bash
   uv run python -c "
   import csv, collections, os
   rows = list(csv.DictReader(open(os.path.join('outputs','time_demo.csv'), encoding='utf-8')))
   print('so moc gio:', len(rows))
   print('route_changed=True:', sum(1 for r in rows if r['route_changed'] == 'True'))
   print('so route khac nhau:', len(collections.Counter(r['path'] for r in rows)))
   "
   ```

   Nếu vẫn chỉ ra 1 route, thử cặp A/B khác (hai POI ở hai quận có `district_factor` lệch nhau nhiều,
   ví dụ Quận 1 ↔ Bình Thạnh) bằng cách điền `CURATED_PAIRS` trong
   [`src/experiments/scenarios.py`](../src/experiments/scenarios.py) — đó là `TODO(P1)`.

---

## Checklist

### Trước mỗi PR (hướng A — bắt buộc)

- [ ] `uv run ruff check` sạch
- [ ] `uv run pytest` → 210 passed, 7 skipped, **0 failed**
- [ ] Nếu sửa `src/search/` hoặc `src/validation/`: coverage hai module vẫn ≥ 95%
- [ ] Nếu sửa `cli.py`: chạy lại bảng exit code ở [A4](#a4-smoke-test-cli-trên-mock)
- [ ] Không thêm `TODO(Px)` mới mà không ghi vào `docs/`

### Trước khi chốt số liệu báo cáo (hướng B)

- [ ] `graph.json` đã commit; `run_all_checks()` rỗng
- [ ] `uv run pytest` → 216 passed, 1 skipped
- [ ] `uv run hcmc validate` exit 0, 3 mode admissible 0 vi phạm, `dynamic_weighted` có phản ví dụ
- [ ] `uv run hcmc experiments --n 120` sinh đủ 7 file
- [ ] `summary.md`: `dynamic_ub` expand ít hơn `zero`; 3 mode admissible đạt `Tối ưu 100.0%`
- [ ] `time_demo.csv` có `route_changed = True` ở ít nhất một mốc giờ
- [ ] Mọi `TODO(Px)` chờ số liệu trong `docs/` đã được điền
- [ ] Mọi số trong báo cáo tái lập được với `seed` trong `configs/default.toml`

---

## Lỗi thường gặp

| Hiện tượng | Nguyên nhân | Cách xử lý |
| --- | --- | --- |
| `ModuleNotFoundError: src` | Chạy ngoài repo root, hoặc chưa sync | `cd` về root, chạy qua `uv run`, hoặc `uv sync` |
| `uv run hcmc` bị block bởi Application Control | Policy chặn exe shim của venv | Dùng `uv run python -m src.cli ...` |
| `'charmap' codec can't encode` | Terminal không phải UTF-8 | `export PYTHONIOENCODING=utf-8` hoặc dùng PowerShell |
| `Không tìm thấy .../graph.json` | Chưa có dữ liệu thật | Thêm `--mock`, hoặc chạy `scripts/build_graph.py` |
| `NotImplementedError: TODO(Px)` | Phần đó chưa ai cài | Xem [scope.md §5](scope.md#5-module-work-package-và-phân-công) biết ai phụ trách |
| `cần một phần chưa được cài đặt (TODO(P6))` | T2 Streamlit chưa làm | Bình thường — T2 là extra (D7) |
| Cài `osmnx`/`geopandas` lỗi | Hai lib này nặng | Chỉ P1, P2 cần. Người khác `uv sync` là đủ |
| `check_admissibility` chạy rất lâu | Graph thật + nhiều goal × mốc giờ | Bình thường (~10 s/mode). Giảm `VALIDATION_GOALS` khi debug |
| `validate` báo LỖI ở dòng `dynamic_weighted` | **Không** tìm được phản ví dụ | Lỗi thật: kiểm `weight_w > 1` trong config và logic heuristic |
| 4 test `test_graph.py` skip vì `networkx` | Chưa cài group `data` | `uv sync --group data`, hoặc bỏ qua ở hướng A |

---

## Tham chiếu

| Tài liệu | Nội dung liên quan |
| --- | --- |
| [scope.md §8](scope.md#8-tiêu-chí-hoàn-thành) | 6 tiêu chí hoàn thành của cả project |
| [algorithm_walkthrough.md §6](algorithm_walkthrough.md) | 5 tiêu chí đạt của WP5 và test tương ứng |
| [heuristic_proof.md](heuristic_proof.md) | Chứng minh toán — bổ trợ cho test lấy mẫu |
| [traffic_model.md](traffic_model.md) | Mô hình FIFO và `fifo_report` |
| [graph_construction.md](graph_construction.md) | Các kiểm tra graph và định dạng `graph.json` |
| [report/README.md](report/README.md) | Checklist trước khi nộp |

> **Một điều cần nhớ về bản chất các kiểm tra:** `check_admissibility`, `check_consistency` và
> `check_fifo` là **bằng chứng lấy mẫu** trên lưới thời gian rời rạc, không phải chứng minh cho mọi thời
> điểm liên tục. Kết quả 0 vi phạm nghĩa là "không tìm thấy vi phạm trên các mẫu đã quét". Chứng minh toán
> nằm ở [heuristic_proof.md](heuristic_proof.md) và hai thứ bổ trợ cho nhau.
