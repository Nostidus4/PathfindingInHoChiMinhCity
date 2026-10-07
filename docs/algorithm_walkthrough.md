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

Dijkstra chính là A\* với $h = 0$ (`search/dijkstra.py`). Có thêm hàm `true_cost(graph, n, goal, t)` trả về
$h^*(n, t)$, dùng để kiểm admissibility.

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

Bảng dưới đây là trace **mong đợi** với `zero` (Dijkstra), xuất phát 08:00 (28800 s):

| Bước | Expand | g (s) | Cập nhật hàng xóm (g mới) | Open sau bước |
| --- | --- | --- | --- | --- |
| 1 | A | 0 | B=100, C=40 | C(40), B(100) |
| 2 | C | 40 | B=70 (tốt hơn 100), D=160, E=140 | B(70), E(140), D(160) |
| 3 | B | 70 | D=120 (tốt hơn 160), E=160 (không tốt hơn) | D(120), E(140) |
| 4 | D | 120 | F=180 | E(140), F(180) |
| 5 | E | 140 | F=210 (không tốt hơn) | F(180) |
| 6 | F | 180 | Tới đích | |

Với `dynamic_ub` trên mock này, $V_{ub} = 10$ m/s nên $h(n) = d_{geo}(n, F) / 10$. Ta có
$h(C) \approx 88.6$, $h(B) \approx 66.3$, $h(D) \approx 49.2$, $h(E) \approx 29.5$ (giây).

- Thứ tự expand là A (f ≈ 109) → C (f ≈ 128.6) → B (f ≈ 136.3) → D (f ≈ 169.2) → E (f ≈ 169.5) → F (f = 180).
- A\* vẫn tìm đúng đường tối ưu, **nhưng vẫn phải expand E**, vì $f(E) \approx 169.5 < 180$.
- Như vậy trên graph nhỏ này, A\* expand **cùng số node** với Dijkstra. Đây chính là rủi ro "graph nhỏ thì
  A\* gần bằng Dijkstra" trong [scope.md §7](scope.md#7-rủi-ro-và-cách-giảm). Để thấy khác biệt rõ ràng phải chạy trên
  graph HCMC khoảng 150 node và lấy trung bình trên nhiều cặp.

> TODO(P5): thay bảng trên bằng output thật của `format_trace()` cho cả `zero` và `dynamic_ub`, sau đó chạy lại trên
> một cặp A/B thật của graph HCMC.

## 5. Validation (M8)

| Kiểm tra | Hàm | Cách làm |
| --- | --- | --- |
| Admissibility | `validation/admissibility.py::check_admissibility` | So $h(n, t)$ với $h^*(n, t)$ do Dijkstra tính, trên nhiều node, goal và mốc thời gian |
| Consistency | `validation/consistency.py::check_consistency` | Kiểm $h(u, t) \le c(u, v, t) + h(v, t + c)$ trên mọi edge và lưới thời gian (mốc 15 phút) |
| Phản ví dụ | `validation/counterexamples.py::find_counterexamples` | Tìm (A, B, t) mà cost của A\* với `dynamic_weighted` lớn hơn cost của Dijkstra |
| FIFO (P3) | `validation/fifo.py::check_fifo` | $t + c(e, t)$ không giảm theo $t$ trên mọi edge |

Chạy tất cả bằng `uv run hcmc validate`. Kết quả ghi vào [heuristic_proof.md §8](heuristic_proof.md#8-kết-quả-kiểm-chứng-bằng-số).

## 6. Tiêu chí đạt của WP5

- [ ] `zero` cho cost bằng Dijkstra trên mọi cặp test.
- [ ] `static_vmax` và `dynamic_ub` cho cost tối ưu và expand ít node hơn `zero`.
- [ ] Không có vi phạm admissibility hay consistency với `zero`, `static_vmax`, `dynamic_ub`.
- [ ] Có ít nhất một phản ví dụ cho `dynamic_weighted`.
- [ ] Không có đường đi (ví dụ A → G trên mock) thì trả `RouteResult(found=False)`, không crash.
