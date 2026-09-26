# Mô hình giao thông phụ thuộc thời gian (M4, WP3)

> Owner: **P3** · Review: P4 · Code: `src/traffic/`, `src/validation/fifo.py` · Tham số: `configs/default.toml`

## 1. Quyết định D2: nguồn traffic

- **Synthetic (Greenshields) là nguồn chính**, vì real-time chỉ cho snapshot hiện tại chứ không cho
  tương lai. Bài toán time-dependent cần biết traffic tại thời điểm xe **sẽ** tới edge.
- **Real-time là optional**, dùng để hiệu chỉnh ρ nếu khảo sát cho thấy có dữ liệu (xem [data_sources.md §8](data_sources.md#8-khảo-sát-dữ-liệu-real-time-r6-optional)).

Mọi nguồn đều đi qua cùng một interface, nên engine không cần biết dữ liệu từ đâu:

```python
class TrafficProvider(Protocol):
    def get_traffic(self, edge_id: str, t: float) -> TrafficState: ...
```

| Provider | File | Vai trò |
| --- | --- | --- |
| `SyntheticProvider(graph, cfg, seed)` | `traffic/synthetic.py` | Nguồn chính, tái lập được nhờ seed |
| `RealSnapshotProvider(path, fallback)` | `traffic/snapshot.py` | Đọc snapshot đã đóng băng (optional) |
| `MockTrafficProvider` | `mocks.py` | Dùng cho test và làm song song |

## 2. Mô hình Greenshields

Ba đại lượng liên kết với nhau qua công thức, **không sinh ngẫu nhiên độc lập** từng cái:

| Đại lượng | Công thức | Đơn vị |
| --- | --- | --- |
| Mật độ | $k(e, t) = k_{jam} \cdot \rho(e, t), \quad \rho \in [0, 1]$ | veh/km |
| Tốc độ | $v = v_{free} \cdot \left(1 - \dfrac{k}{k_{jam}}\right)$ | km/h |
| Lưu lượng | $q = k \cdot v$ | veh/h |
| Capacity | $q_{max} = \dfrac{v_{free} \cdot k_{jam}}{4}$ (đạt tại $k = k_{jam}/2$) | veh/h |

Các hàm thuần tương ứng nằm trong `traffic/greenshields.py`: `speed`, `flow`, `capacity`, `density_from_ratio`.

**Vì sao cần flow:** hai trạng thái có cùng $q$ có thể là "thông thoáng" ($k$ nhỏ, $v$ lớn) hoặc "kẹt"
($k$ lớn, $v$ nhỏ). Nhìn tỷ số $q / q_{max}$ cùng với $k$ sẽ phân biệt được hai nhánh này.

## 3. Profile ρ(e, t)

ρ(e, t) được sinh từ ba thành phần:

$$
\rho(e, t) = \text{clamp}\Big(\rho_{base} \cdot \big(1 + P(t)\big) \cdot f_{road}(e) \cdot f_{district}(e),\ 0,\ 1\Big)
$$

- $P(t)$: profile theo giờ, có **đỉnh buổi sáng và buổi chiều**, thấp vào ban đêm. Mỗi đỉnh là một hàm mượt
  (ví dụ Gaussian) với tâm, độ rộng và biên độ lấy từ `[peaks]`.
- $f_{road}$: hệ số theo loại đường.
- $f_{district}$: hệ số theo quận, lấy từ `[district_factor]`.

Tham số khởi điểm (`configs/default.toml`). **Các giá trị này cần hiệu chỉnh và ghi lại lý do:**

| Tham số | Giá trị | Ghi chú |
| --- | --- | --- |
| `k_jam_veh_km` | 150 | Mật độ kẹt xe |
| `min_speed_kmh` | 5 | Chặn dưới, để thời gian đi không vô hạn |
| `free_flow_kmh` | primary 50, secondary 40, tertiary 35, residential 25 | Profile xe máy (D4) |
| Đỉnh sáng | 07:30, rộng 90 phút, biên độ 0.7 | |
| Đỉnh chiều | 17:30, rộng 120 phút, biên độ 0.8 | |
| `base_density_ratio` | 0.2 | ρ lúc thấp điểm |
| `district_factor` | Q1 1.3, Q3 1.2, Q5 1.15, Phú Nhuận 1.1, Bình Thạnh 1.0 | |

> TODO(P3): giải thích cơ sở chọn từng giá trị (tài liệu tham khảo, quan sát thực tế, hoặc dữ liệu real-time nếu có).

### Quy ước thời gian

- Thời điểm tính bằng **giây kể từ 00:00** (`src/timeutil.py`).
- Tính trên **lưới 15 phút** (`GRID_STEP = 900`), giữa các mốc thì **nội suy tuyến tính**.
- Ngoài cửa sổ mô phỏng (`window_start` đến `window_end`) thì **giữ giá trị biên** (clamp).

### Tái lập

`SyntheticProvider(graph, cfg, seed)` có thể thêm nhiễu nhỏ cho từng edge, nhưng **cùng seed phải cho cùng
kết quả**. Điều này được kiểm trong `tests/test_synthetic_provider.py`.

## 4. Effective speed (D5, phần này do P4 cài)

$$
v_{\text{eff}} = v_{free} \cdot \left(1 - \frac{k}{k_{jam}}\right), \text{ giới hạn thêm theo capacity } (q / q_{max})
$$

BPR là mode phụ. Chi tiết và việc đổi đơn vị nằm trong `src/cost/speed_model.py`, là **nơi duy nhất đổi đơn vị**
(km/h sang m/s).

## 5. FIFO

**Điều kiện FIFO:** xuất phát muộn hơn thì không bao giờ tới sớm hơn:

$$
t_1 < t_2 \implies t_1 + c(e, t_1) \le t_2 + c(e, t_2) \quad \forall e
$$

FIFO là điều kiện để time-dependent Dijkstra và A\* cho kết quả đúng.

- **Bảo đảm bằng thiết kế:** profile mượt, không có bước nhảy đột ngột.
- **Kiểm bằng test số:** `validation/fifo.py::check_fifo` quét mọi edge trên lưới thời gian (`tests/test_fifo.py`).

> TODO(P3): báo cáo kết quả kiểm FIFO, ghi rõ số edge đã kiểm, số vi phạm và độ dốc lớn nhất của $c(e, t)$.

## 6. SpeedBounds: bảng tốc độ tính trước cho P4

Heuristic cần $V_{ub}(t)$, tức là tốc độ lớn nhất trên **mọi edge** ở **mọi thời điểm ≥ t**. Nếu P4 tự gọi
`get_traffic` thì phải gọi hàng nghìn lần mỗi lần tính heuristic. Vì vậy P3 tính trước **một lần** trong
`traffic/speed_bounds.py`:

| Trường | Định nghĩa | Dùng cho |
| --- | --- | --- |
| `v_max` | $\max_{e, t} v_{\text{eff}}(e, t)$ | `static_vmax` |
| `v_ub(t)` | $\max_{t' \ge t}\ \max_e v_{\text{eff}}(e, t')$ (suffix max), nội suy giữa các mốc | `dynamic_ub` |
| `v_mean(t)` | Trung bình $v_{\text{eff}}(e, t)$ trên mọi edge | `dynamic_weighted` |

**Tính chất bắt buộc của `v_ub`** (kiểm trong `tests/test_speed_bounds.py`):

1. **Không tăng** theo $t$.
2. $v_{ub}(t) \ge v_{\text{eff}}(e, t')$ với mọi $e$ và mọi $t' \ge t$.

> **Lưu ý khi nội suy:** nội suy tuyến tính giữa hai mốc của một dãy không tăng vẫn cho ra hàm không tăng.
> Nhưng giá trị nội suy phải vẫn ≥ tốc độ thật tại mọi điểm **giữa** hai mốc. Vì tốc độ thật cũng được
> nội suy tuyến tính trên cùng lưới, nên điều này đúng khi cả hai dùng chung lưới.

## 7. Đầu ra cho báo cáo

> TODO(P3):
>
> - Biểu đồ ρ(t), v(t), q(t) cho vài edge tiêu biểu (primary ở Q1, residential ở Bình Thạnh).
> - Biểu đồ `v_ub(t)` so với `v_mean(t)`.
> - Bảng tham số cuối cùng sau khi hiệu chỉnh.
