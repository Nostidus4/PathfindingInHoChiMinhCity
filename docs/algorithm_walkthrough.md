# Thuật toán và giải thích từng bước (M7, M8, WP5)

> Owner: **P5** · Review: P6 · Code: `src/search/`, `src/validation/`

## 1. Time-dependent A\*

**Điểm khác với A\* thông thường:** chi phí edge phụ thuộc thời điểm xe tới edge đó. Khi mở rộng node $u$,
xe đang ở thời điểm $t_u = t_0 + g(u)$, nên chi phí sang $v$ là $c(u, v, t_u)$.

```text
function TD-ASTAR(G, A, B, t0, c, h):
    g[A] ← 0 ; parent[A] ← nil
    OPEN ← {(f = h(A, t0), A)} ; CLOSED ← ∅
    while OPEN ≠ ∅:
        u ← OPEN.pop_min_f()
        if u = B: return RECONSTRUCT(parent, B)
        if u ∈ CLOSED: continue
        CLOSED ← CLOSED ∪ {u}
        t_u ← t0 + g[u]
        for each edge e = (u, v):
            g' ← g[u] + c(e, t_u)
            if g' < g[v]:
                g[v] ← g' ; parent[v] ← u
                OPEN.push(f = g' + h(v, t0 + g'), v)
    return NO_PATH
```

**Các thành phần:**

- Open set là priority queue (`heapq`) sắp theo $f$. Tie-break ổn định (ưu tiên $h$ nhỏ, sau đó đến thứ tự đưa vào)
  để kết quả tái lập được.
- Closed set, `g`, `parent`, và $t_n = t_0 + g(n)$. Cuối cùng dựng lại đường đi từ `parent`.
- **Tính đúng:** cần FIFO (A4) và heuristic consistent. Khi đó node được lấy ra khỏi OPEN đã có $g$ tối ưu.
  Nếu heuristic chỉ admissible, hoặc không admissible như `dynamic_weighted`, thì kết quả có thể không tối ưu.
  Đây chính là thứ `counterexamples.py` đo.

**Engine độc lập:** hàm `astar(graph, start, goal, departure_time, edge_cost, heuristic, trace)` nhận
`edge_cost` và `heuristic` dưới dạng **hàm**. Engine không biết traffic đến từ đâu và không import UI.
Chữ ký dễ dùng hơn nằm ở facade:

```python
Pathfinder(graph, provider, cfg).route(start, goal, departure_time, heuristic_mode, trace)
```

## 2. Time-dependent Dijkstra (ground truth)

Về lý thuyết Dijkstra chính là A\* với $h = 0$, nhưng `search/dijkstra.py` được cài **độc lập**, không gọi
`astar()`. Lý do: `validation/` dùng Dijkstra làm đáp án để kiểm A\*. Nếu oracle gọi lại chính engine đang
được kiểm thì một lỗi trong `astar` sẽ xuất hiện ở cả hai bên và test vẫn xanh. Hai cài đặt tách rời biến
`check_admissibility` / `find_counterexamples` thành phép **kiểm chéo** thật sự; việc hai bên cho cùng kết quả
được khẳng định bằng `tests/test_astar.py::test_zero_mode_matches_independent_dijkstra` (36 cặp x 3 mốc giờ).

Module cung cấp ba hàm:

| Hàm | Dùng để |
| --- | --- |
| `dijkstra(graph, start, goal, t, edge_cost)` | Đường tối ưu một cặp, dừng sớm khi settle goal |
| `earliest_arrival_times(graph, source, t, edge_cost)` | Một lần quét -> chi phí tối ưu tới **mọi** node |
| `true_cost(graph, n, goal, t, edge_cost)` | $h^*(n, t)$ để kiểm admissibility; `inf` nếu không có đường |

`check_admissibility` dùng `earliest_arrival_times`, nên chỉ cần $|nodes| \times |times|$ lần Dijkstra thay vì
$|nodes| \times |goals| \times |times|$.

## 3. Trace mode (D8)

Engine ghi lại mọi bước **ngay từ đầu**, không phải thêm vào sau. Mỗi `TraceStep` gồm:

| Trường | Ý nghĩa |
| --- | --- |
| `step` | Số thứ tự bước |
| `action` | `expand`, `push`, `update`, `skip` |
| `node` | Node đang xét |
| `g`, `h`, `f` | Giá trị tại bước đó (giây) |
| `t` | Thời điểm xe tới node |
| `open_size` | Kích thước open set |

Bật trace bằng lệnh:

```bash
uv run hcmc route --start A --goal F --time 08:00 --heuristic dynamic_ub --trace
```

## 4. Ví dụ từng bước trên mock graph

Graph trong `src/mocks.py` có tốc độ hằng 36 km/h, tức 10 m/s, nên cost của mỗi edge bằng `length / 10` giây.

```text
        G --(1 chiều)--> A --1000-- B --500-- D --600-- F
                         |        / |         |        /
                        400    300  900     1200    700
                         |    /     |         |    /
                         C ---------+-- 1000 -- E
```

Đáp án biết trước: **A → C → B → D → F**, dài 1800 m, mất 180 s.

Dưới đây là output thật của `format_trace()` với `MockTrafficProvider` (tốc độ hằng 10 m/s), xuất phát
08:00. Sinh lại bằng:

```bash
uv run hcmc route --mock --start A --goal F --time 08:00 --heuristic zero --trace
```

```text
 #  action  node  g (s)  h (s)  f (s)         t  open  note
--  ------  ----  -----  -----  -----  --------  ----  ---------------------------
 0  expand  A       0.0    0.0    0.0  08:00:00     0
 1  push    B     100.0    0.0  100.0  08:01:40     1
 2  push    C      40.0    0.0   40.0  08:00:40     2
 3  expand  C      40.0    0.0   40.0  08:00:40     1
 4  update  B      70.0    0.0   70.0  08:01:10     2
 5  push    D     160.0    0.0  160.0  08:02:40     3
 6  push    E     140.0    0.0  140.0  08:02:20     4
 7  expand  B      70.0    0.0   70.0  08:01:10     3
 8  update  D     120.0    0.0  120.0  08:02:00     4
 9  skip    B     100.0    0.0  100.0  08:01:40     3  nhãn cũ, đã có nhãn tốt hơn
10  expand  D     120.0    0.0  120.0  08:02:00     2
11  push    F     180.0    0.0  180.0  08:03:00     3
12  expand  E     140.0    0.0  140.0  08:02:20     2
13  skip    D     160.0    0.0  160.0  08:02:40     1  nhãn cũ, đã có nhãn tốt hơn
14  expand  F     180.0    0.0  180.0  08:03:00     0

Tổng: 15 bước, 6 lần expand.
```

Đọc bảng: bước 4 là `update` B (70 < 100 tìm được ở bước 1), nên bước 9 pop phải nhãn B cũ và `skip`.
Kết quả **A → C → B → D → F**, 1800 m, 180 s — khớp `MOCK_OPTIMA`.

Với `dynamic_ub` trên mock này, $V_{ub} = 10$ m/s nên $h(n) = d_{geo}(n, F) / 10$. Trace thật cho
$h(A) = 109.1$, $h(C) = 88.5$, $h(B) = 66.3$, $h(D) = 49.2$, $h(E) = 29.5$ (giây):

```text
 #  action  node  g (s)  h (s)  f (s)         t  open  note
--  ------  ----  -----  -----  -----  --------  ----  ---------------------------
 0  expand  A       0.0  109.1  109.1  08:00:00     0
 1  push    B     100.0   66.3  166.3  08:01:40     1
 2  push    C      40.0   88.5  128.5  08:00:40     2
 3  expand  C      40.0   88.5  128.5  08:00:40     1
 4  update  B      70.0   66.3  136.3  08:01:10     2
 5  push    D     160.0   49.2  209.2  08:02:40     3
 6  push    E     140.0   29.5  169.5  08:02:20     4
 7  expand  B      70.0   66.3  136.3  08:01:10     3
 8  update  D     120.0   49.2  169.2  08:02:00     4
 9  skip    B     100.0   66.3  166.3  08:01:40     3  nhãn cũ, đã có nhãn tốt hơn
10  expand  D     120.0   49.2  169.2  08:02:00     2
11  push    F     180.0    0.0  180.0  08:03:00     3
12  expand  E     140.0   29.5  169.5  08:02:20     2
13  expand  F     180.0    0.0  180.0  08:03:00     1

Tổng: 14 bước, 6 lần expand.
```

- Thứ tự expand: A → C → B → D → E → F, vẫn tìm đúng đường tối ưu.
- **Vẫn phải expand E**, vì $f(E) = 169.5 < 180$.
- Như vậy trên graph nhỏ này, A\* expand **cùng số node** với Dijkstra (6/6). Đây chính là rủi ro "graph nhỏ thì
  A\* gần bằng Dijkstra" trong [scope.md §7](scope.md#7-rủi-ro-và-cách-giảm).

Khác biệt xuất hiện khi traffic làm các cạnh lệch nhau. Với `SyntheticProvider` (Greenshields theo loại đường
và quận), cặp C → D lúc 17:30:

```text
zero               cost= 135.24  expanded=5  C>B>D
static_vmax        cost= 135.24  expanded=3  C>B>D
dynamic_ub         cost= 135.24  expanded=3  C>B>D
dynamic_weighted   cost= 151.16  expanded=2  C>D      <- vượt tối ưu 11.77%
```

Hai heuristic admissible cắt được 5 → 3 node mà vẫn tối ưu; `dynamic_weighted` expand ít nhất (2) nhưng
**chọn sai đường**. Xem lại bằng:

```bash
uv run hcmc compare --mock --start C --goal D --time 17:30
```

## 5. Validation (M8)

| Kiểm tra | Hàm | Cách làm |
| --- | --- | --- |
| Admissibility | `validation/admissibility.py::check_admissibility` | So $h(n, t)$ với $h^*(n, t)$ do Dijkstra tính, trên nhiều node, goal và mốc thời gian |
| Consistency | `validation/consistency.py::check_consistency` | Kiểm $h(u, t) \le c(u, v, t) + h(v, t + c)$ trên mọi edge và lưới thời gian (mốc 15 phút) |
| Phản ví dụ | `validation/counterexamples.py::find_counterexamples` | Tìm (A, B, t) mà cost của A\* với `dynamic_weighted` lớn hơn cost của Dijkstra |
| FIFO (P3) | `validation/fifo.py::check_fifo` | $t + c(e, t)$ không giảm theo $t$ trên mọi edge |

Chạy tất cả bằng `uv run hcmc validate`. Kết quả ghi vào [heuristic_proof.md §8](heuristic_proof.md#8-kết-quả-kiểm-chứng-bằng-số).

## 6. Tiêu chí đạt của WP5

- [x] `zero` cho cost bằng Dijkstra trên mọi cặp test (`test_zero_mode_matches_independent_dijkstra`).
- [x] `static_vmax` và `dynamic_ub` cho cost tối ưu và expand **không nhiều hơn** `zero`
      (`test_admissible_heuristics_expand_at_most_as_many_nodes`). Trên mock 7 node có cặp bằng nhau; chênh
      lệch thật phải đo trên graph HCMC.
- [x] Không có vi phạm admissibility hay consistency với `zero`, `static_vmax`, `dynamic_ub`
      (`tests/test_admissibility.py`, `tests/test_consistency.py`).
- [x] Có ít nhất một phản ví dụ cho `dynamic_weighted` (`tests/test_counterexamples.py`; `w = 1.5` trong
      `configs/default.toml` đã đủ sinh phản ví dụ trên mock).
- [x] Không có đường đi (A → G trên mock) thì trả `RouteResult(found=False)`, không crash
      (`test_no_path_returns_found_false`).

Các kiểm tra trên là **bằng chứng lấy mẫu** trên fixture mock, không thay cho chứng minh toán
([heuristic_proof.md](heuristic_proof.md)) và không chứng minh FIFO trên toàn miền liên tục. Khi WP2 commit
`data/processed/graph.json`, chạy lại `uv run hcmc validate` (không có `--mock`) trên graph thật.
