# Cost model và heuristic: chứng minh (M5, M6, WP4)

> Owner: **P4** · Review: P3 · Code: `src/cost/` · Kiểm chứng số: `src/validation/` (P5)

Đây là phần lõi toán, dùng để trả lời R2 (heuristic không phải hằng số) và R5 (có admissible và consistent không).

## 1. Edge cost

$$
c(u, v, t) = \frac{\text{length}(u, v)}{v_{\text{eff}}(e, t)} \quad \text{(giây)}
$$

- `length` tính bằng mét, $v_{\text{eff}}$ tính bằng m/s. Việc đổi đơn vị chỉ làm trong `cost/speed_model.py`.
- $t$ là thời điểm xe **vào** edge: $t = t_0 + g(u)$.
- Mode `distance` (baseline phụ): $c(u, v) = \text{length}(u, v)$, không phụ thuộc $t$.

Code: `cost/edge_cost.py::edge_cost(segment, t, provider, mode)`.

## 2. Bốn heuristic (D6 ✅)

$d_{geo}(n, B)$ là khoảng cách haversine từ $n$ tới đích $B$.

| Mode | Công thức | Vai trò | Kỳ vọng |
| --- | --- | --- | --- |
| `zero` | $h = 0$ | Ground truth (Dijkstra) | Admissible, consistent |
| `static_vmax` | $d_{geo}(n, B) / v_{max}$ | Baseline hằng số | Admissible, consistent, nhưng yếu |
| `dynamic_ub` | $d_{geo}(n, B) / V_{ub}(t)$ | **Heuristic chính**, động | Admissible, consistent (chứng minh ở §4, §5) |
| `dynamic_weighted` | $w \cdot d_{geo}(n, B) / V_{now}(t),\ w > 1$ | Phản ví dụ | **Cố tình inadmissible** |

Trong đó:

$$
V_{ub}(t) = \max_{t' \ge t}\ \max_{e \in E}\ v_{\text{eff}}(e, t') \qquad \text{(suffix max theo thời gian)}
$$

$V_{now}(t)$ là tốc độ trung bình toàn mạng tại thời điểm $t$ (`SpeedBounds.v_mean`).

**Vì sao cần 4 mode:**

- `dynamic_ub` đáp ứng R2 và trả lời "có" cho R5, kèm chứng minh.
- `dynamic_weighted` cho câu trả lời "không" kèm ca cụ thể, nhờ vậy báo cáo trả lời được cả hai chiều.
- `zero` và `static_vmax` là mốc để so expanded nodes và runtime.

**R2 được đáp ứng thế nào:** $V_{ub}$ tính từ $v_{\text{eff}}$, mà $v_{\text{eff}}$ lại phụ thuộc
density và flow. $V_{ub}$ cũng phụ thuộc $t$. Vì vậy $h(n, t)$ **không phải hằng số tại POI**: cùng một node
nhưng đổi giờ thì $h$ thay đổi.

Code: heuristic là **object**, được tạo một lần bằng `make_heuristic(mode, graph, bounds, params)` và gọi dưới
dạng `h(node, goal, t)`. Object này đọc `SpeedBounds` đã tính trước, không gọi provider mỗi lần.

## 3. Các giả thiết

Chứng minh dựa trên ba giả thiết. Mỗi giả thiết đều có test tự động kiểm tra:

| # | Giả thiết | Được bảo đảm bởi |
| --- | --- | --- |
| A1 | $\text{length}(u, v) \ge d_{geo}(u, v)$ với mọi edge | `graph/checks.py::check_length_vs_haversine` |
| A2 | $v_{\text{eff}}(e, t') \le V_{ub}(t)$ với mọi $e$ và mọi $t' \ge t$ | Định nghĩa suffix max, `tests/test_speed_bounds.py` |
| A3 | $V_{ub}$ không tăng theo $t$ | Định nghĩa suffix max, `tests/test_speed_bounds.py` |
| A4 | FIFO | `validation/fifo.py` (cần cho tính đúng của time-dependent A\*) |

## 4. Admissibility của `dynamic_ub`

**Mệnh đề.** Với mọi node $n$, mọi đích $B$ và mọi thời điểm $t$: $h(n, t) \le h^*(n, t)$, trong đó
$h^*(n, t)$ là thời gian tối ưu thật từ $n$ tới $B$ khi xuất phát lúc $t$.

**Chứng minh.** Xét một đường đi bất kỳ $n = x_0 \to x_1 \to \dots \to x_m = B$, xuất phát lúc $t$. Gọi
$t_i$ là thời điểm vào edge thứ $i$, ta có $t_i \ge t$.

- Tổng chiều dài đường đi $\ge \sum_i d_{geo}(x_i, x_{i+1}) \ge d_{geo}(n, B)$. Bất đẳng thức thứ nhất
  theo A1, bất đẳng thức thứ hai theo bất đẳng thức tam giác.
- Trên mỗi edge, xe chạy với tốc độ $v_{\text{eff}}(e_i, t_i) \le V_{ub}(t)$ (theo A2, vì $t_i \ge t$).

Do đó thời gian đi $\displaystyle\sum_i \frac{\text{length}_i}{v_{\text{eff}}(e_i, t_i)} \ge \frac{\sum_i
\text{length}_i}{V_{ub}(t)} \ge \frac{d_{geo}(n, B)}{V_{ub}(t)} = h(n, t)$.

Bất đẳng thức đúng với mọi đường đi, nên cũng đúng với đường tối ưu. Vậy $h(n, t) \le h^*(n, t)$. ∎

`static_vmax` admissible theo cùng lập luận, vì $v_{max} = V_{ub}(t_{start}) \ge V_{ub}(t)$.
`zero` thì hiển nhiên admissible.

## 5. Consistency (dạng time-dependent) của `dynamic_ub`

**Mệnh đề.** Với mọi edge $(u, v)$ và mọi $t$, gọi $c = c(u, v, t)$, ta có

$$
h(u, t) \le c + h(v, t + c).
$$

**Chứng minh.**

1. Bất đẳng thức tam giác: $d_{geo}(u, B) \le d_{geo}(u, v) + d_{geo}(v, B)$.
2. $c = \dfrac{\text{length}(u, v)}{v_{\text{eff}}(e, t)} \ge \dfrac{d_{geo}(u, v)}{V_{ub}(t)}$, theo A1 và A2.
3. Chia bước 1 cho $V_{ub}(t)$ rồi áp bước 2:
   $h(u, t) = \dfrac{d_{geo}(u, B)}{V_{ub}(t)} \le c + \dfrac{d_{geo}(v, B)}{V_{ub}(t)}$.
4. Theo A3, $V_{ub}(t + c) \le V_{ub}(t)$, nên $\dfrac{d_{geo}(v, B)}{V_{ub}(t)} \le \dfrac{d_{geo}(v, B)}{V_{ub}(t + c)} = h(v, t + c)$.

Ghép bước 3 và bước 4 được điều cần chứng minh. ∎

> **Điểm mấu chốt nằm ở bước 4.** Nếu $V_{ub}$ có thể **tăng** theo thời gian thì bước 4 sai. Đó là lý do
> phải dùng suffix max thay vì $\max_e v_{\text{eff}}(e, t)$ tại đúng thời điểm $t$.

`static_vmax` là trường hợp riêng khi $V_{ub}$ là hằng số. `zero` consistent vì $0 \le c + 0$.

## 6. `dynamic_weighted` không admissible

$h_w(n, t) = w \cdot d_{geo}(n, B) / V_{now}(t)$ với $w > 1$ và $V_{now}(t) \le V_{ub}(t)$, nên

$$
h_w(n, t) \ge w \cdot h_{\text{dynamic\_ub}}(n, t).
$$

Khi xét một edge gần như thẳng ($\text{length} \approx d_{geo}$) chạy ở tốc độ gần $V_{ub}$, chi phí thật
xấp xỉ $h_{\text{dynamic\_ub}}$, tức là nhỏ hơn $h_w$. Khi đó $h_w > h^*$, nên heuristic vi phạm
admissibility, và A\* có thể trả về đường không tối ưu.

Kiểm chứng: `validation/counterexamples.py::find_counterexamples` trích ra ca cụ thể (A, B, thời điểm) mà
cost của A\* lớn hơn cost của Dijkstra.

> TODO(P4/P5): chèn ca phản ví dụ thật (A, B, giờ, cost A\*, cost Dijkstra, hai route vẽ trên bản đồ).

## 7. Trade-off của suffix max

Suffix max kéo cả những thời điểm thông thoáng ở **cuối** cửa sổ mô phỏng (ví dụ ban đêm) vào $V_{ub}$.
Vì vậy bound có thể yếu vào ban ngày, lúc đó `dynamic_ub` gần bằng `static_vmax`.

- Cần đo thực tế trong experiment: so expanded nodes của `dynamic_ub` với `static_vmax` theo từng giờ xuất phát.
- Nếu bound quá yếu, có thể thu hẹp cửa sổ mô phỏng (`window_end` trong config), hoặc dùng biến thể dưới đây.

**Tuỳ chọn `dynamic_ub_window`** (nếu dư thời gian): dùng cửa sổ trượt $[t, t + T]$ thay cho $[t, \infty)$.
Bound chặt hơn, nhưng $V_{ub}$ không còn đơn điệu, nên **consistency có thể bị vi phạm** vì bước 4 sai.
Admissibility vẫn giữ được nếu mọi đường đi tới $B$ đều kết thúc trước $t + T$. Đo bằng
`validation/consistency.py`. Đây là phân tích thú vị để đưa vào báo cáo.

## 8. Kết quả kiểm chứng bằng số

> TODO(P5): điền sau khi chạy `uv run hcmc validate`.
>
> | Mode | Admissibility (vi phạm / số lần kiểm) | Consistency (vi phạm / số lần kiểm) |
> | --- | --- | --- |
> | `zero` | | |
> | `static_vmax` | | |
> | `dynamic_ub` | | |
> | `dynamic_weighted` | | |
