# Mô hình giao thông phụ thuộc thời gian (M4, WP3)

> Owner: **P3** · Review: P4 · Code: `src/traffic/`, `src/validation/fifo.py` · Tham số: `configs/default.toml`

## 0. Bản đồ WP3 → code

| Sub-WP | Nội dung | Code | Test |
| --- | --- | --- | --- |
| WP3.1 Contract | `TrafficState`, `TrafficProvider`, tham số | `models.py` (dùng chung, không đổi), `traffic/base.py`, `config.py` (`SimConfig`) | `test_synthetic_provider.py` |
| WP3.2 Profile ρ | daily / road type / area / ρ(e, t) | `traffic/profiles.py` | `test_traffic_profiles.py` |
| WP3.3 Greenshields | density, speed, flow, `get_traffic` | `traffic/greenshields.py`, `traffic/synthetic.py` | `test_greenshields.py`, `test_synthetic_provider.py` |
| WP3.4 Thời gian + aggregate | normalize, slot 15 phút, nội suy, clamp, bảng tốc độ mạng | `traffic/timeslots.py`, `traffic/speed_bounds.py`, `SyntheticProvider.speed_table()` | `test_timeslots.py`, `test_speed_bounds.py` |
| WP3.5 Validation + FIFO | range, `q = k·v`, biến thiên theo giờ, nội suy, FIFO | `traffic/checks.py`, `validation/fifo.py` | `test_fifo.py` và các file trên |

Tên trường của `TrafficState` theo contract chung trong `models.py`:

| Tên trong đặc tả WP3 | Trường của `TrafficState` | Đơn vị |
| --- | --- | --- |
| `vehicle_density` | `density_veh_km` | veh/km |
| `average_speed` | `speed_kmh` | km/h |
| `flow_rate` | `flow_veh_h` | veh/h |
| (thêm) capacity | `capacity_veh_h` | veh/h |

Tên các thành phần trong outline WP3 tương ứng với code như sau: `TrafficConfig` là `SimConfig`.
`GreenshieldsTrafficProvider` là `SyntheticProvider`. `compute_density/speed/flow` là
`greenshields.density_from_ratio / speed / flow`. `get_density_ratio(edge, time)` là
`SyntheticProvider.get_density_ratio`. `network_max_speed[time]` là `SpeedBounds.network_max_speed(t)`.
`traffic_speed_table[time]` là `SyntheticProvider.speed_table()`.

## 1. Quyết định D2: nguồn traffic

- **Synthetic (Greenshields) là nguồn chính**, vì real-time chỉ cho snapshot hiện tại chứ không cho
  tương lai. Bài toán time-dependent cần biết traffic tại thời điểm xe **sẽ** tới edge.
- **Real-time là optional**, dùng để hiệu chỉnh ρ nếu khảo sát cho thấy có dữ liệu (xem [data_sources.md §8](data_sources.md#8-khảo-sát-dữ-liệu-real-time-r6-optional)).
  `traffic/snapshot.py` vẫn là stub.

Mọi nguồn đều đi qua cùng một interface, nên engine không cần biết dữ liệu từ đâu:

```python
class TrafficProvider(Protocol):
    def get_traffic(self, edge_id: str, t: float) -> TrafficState: ...
```

| Provider | File | Vai trò |
| --- | --- | --- |
| `SyntheticProvider(graph, cfg, seed)` | `traffic/synthetic.py` | Nguồn chính, tái lập được nhờ seed |
| `RealSnapshotProvider(path, fallback)` | `traffic/snapshot.py` | Đọc snapshot đã đóng băng (optional, chưa làm) |
| `MockTrafficProvider` | `mocks.py` | Dùng cho test và làm song song |

## 2. Mô hình Greenshields

Ba đại lượng liên kết với nhau qua công thức, **không sinh ngẫu nhiên độc lập** từng cái:

| Đại lượng | Công thức | Đơn vị |
| --- | --- | --- |
| Mật độ | $k(e, t) = k_{jam} \cdot \rho(e, t), \quad \rho \in [0, 1]$ | veh/km |
| Tốc độ | $v = \max\left(v_{min},\ v_{free} \cdot \left(1 - \dfrac{k}{k_{jam}}\right)\right)$ | km/h |
| Lưu lượng | $q = k \cdot v$ | veh/h |
| Capacity | $q_{max} = \dfrac{v_{free} \cdot k_{jam}}{4}$ (đạt tại $k = k_{jam}/2$) | veh/h |

Các hàm thuần tương ứng nằm trong `traffic/greenshields.py`: `speed`, `flow`, `capacity`, `density_from_ratio`,
`state_from_ratio`.

- `q = k · v` luôn đúng chính xác, kể cả khi tốc độ bị chặn ở $v_{min}$, vì `q` tính từ chính `v` đã chặn.
- `q ≤ q_max` luôn đúng. Không chặn thì $q = k \cdot v$ đạt cực đại $q_{max}$ tại $k_{jam}/2$. Khi bị chặn
  thì $q \le k_{jam} \cdot v_{min} = 750 < q_{max}$ (vì $v_{free} \ge 20$ km/h). Hệ quả là
  `cost/speed_model.effective_speed` của P4 **không bao giờ phạt capacity** với `SyntheticProvider`, nên
  $v_{\text{eff}}$ = `speed_kmh`. Điều này được kiểm trong `test_no_capacity_penalty_in_speed_model`.

**Vì sao cần flow:** hai trạng thái có cùng $q$ có thể là "thông thoáng" ($k$ nhỏ, $v$ lớn) hoặc "kẹt"
($k$ lớn, $v$ nhỏ). Nhìn tỷ số $q / q_{max}$ cùng với $k$ sẽ phân biệt được hai nhánh này.

## 3. Profile ρ(e, t)

$$
\rho(e, t) = \text{clamp}\Big(\rho_{base} \cdot \big(1 + P(t)\big) \cdot f_{road}(e) \cdot f_{district}(e) \cdot \varepsilon(e),\ 0,\ 1\Big)
$$

- $P(t) = \sum_i a_i \exp\left(-\dfrac{(t - c_i)^2}{2\sigma_i^2}\right)$ là tổng các đỉnh Gaussian. Tâm $c_i$,
  biên độ $a_i$ và độ rộng lấy từ `[peaks]`, với $\sigma_i$ = `width_min / 2`, tức là `width_min` là độ dài
  khoảng $[c - \sigma, c + \sigma]$.
- $f_{road}$: hệ số theo loại đường, lấy từ `[road_type_factor]`. Loại đường lạ dùng `default`.
- $f_{district}$: hệ số theo quận, lấy từ `[district_factor]`. Quận lạ dùng 1.0.
- $\varepsilon(e)$: nhiễu **cố định theo edge**, nằm trong $[1 - \text{edge\_noise}, 1 + \text{edge\_noise}]$, sinh
  từ chuỗi `"seed:edge_id"`. Nhiễu này không đổi theo thời gian nên profile vẫn mượt.

Tham số khởi điểm (`configs/default.toml`):

| Tham số | Giá trị | Cơ sở chọn |
| --- | --- | --- |
| `k_jam_veh_km` | 150 | Mật độ kẹt quy đổi cho một làn. Chỉ ảnh hưởng độ lớn của k và q, không ảnh hưởng tốc độ (v chỉ phụ thuộc ρ) |
| `min_speed_kmh` | 5 | Tốc độ đi bộ dắt xe. Chặn dưới để thời gian đi hữu hạn. Với tham số hiện tại thì không bao giờ chạm tới |
| `free_flow_kmh` | primary 50, secondary 40, tertiary 35, residential 25 | Tốc độ xe máy khi đường trống, xấp xỉ giới hạn tốc độ nội đô (D4) |
| Đỉnh sáng | 07:30, rộng 90 phút, biên độ 0.7 | Giờ đi làm / đi học |
| Đỉnh trưa | 12:00, rộng 240 phút, biên độ 0.25 | Ban ngày đông hơn sáng sớm / đêm (đặc tả: "thấp ban đêm") |
| Đỉnh chiều | 17:30, rộng 120 phút, biên độ 0.8 | Giờ tan tầm, kéo dài và nặng hơn buổi sáng |
| `base_density_ratio` | 0.2 | ρ lúc thấp điểm |
| `road_type_factor` | primary 1.2, secondary 1.1, tertiary 1.0, residential 0.8 | Trục chính hút nhiều xe hơn hẻm / đường nội khu |
| `district_factor` | Q1 1.3, Q3 1.2, Q5 1.15, Phú Nhuận 1.1, Bình Thạnh 1.0 | Quận trung tâm đông hơn |
| `edge_noise` | 0.1 | Để hai edge cùng loại đường và cùng quận không giống hệt nhau |

> Các giá trị trên là **ước lượng khởi điểm theo định tính**, chưa hiệu chỉnh bằng dữ liệu đo thực tế.
> Nếu khảo sát real-time (R6) có dữ liệu thì dùng để hiệu chỉnh `base_density_ratio`, biên độ đỉnh và hệ số quận.

Kết quả với tham số trên (tắt nhiễu, dạng ρ / tốc độ km/h):

| Edge | 05:00 | 07:30 | 12:00 | 17:30 | 23:00 |
| --- | --- | --- | --- | --- | --- |
| primary, Quận 1 | 0.31 / 34.3 | 0.54 / 23.2 | 0.39 / 30.5 | 0.56 / 21.8 | 0.31 / 34.4 |
| primary, Bình Thạnh | 0.24 / 38.0 | 0.41 / 29.4 | 0.30 / 35.0 | 0.43 / 28.3 | 0.24 / 38.0 |
| residential, Quận 1 | 0.21 / 19.8 | 0.36 / 16.1 | 0.26 / 18.5 | 0.38 / 15.6 | 0.21 / 19.8 |
| residential, Bình Thạnh | 0.16 / 21.0 | 0.28 / 18.1 | 0.20 / 20.0 | 0.29 / 17.8 | 0.16 / 21.0 |

### Quy ước thời gian (`traffic/timeslots.py`)

- Thời điểm tính bằng **giây kể từ 00:00** (`src/timeutil.py`).
- ρ được tính tại các mốc của **lưới 15 phút** (`TimeGrid`, mặc định 05:00, 05:15, ..., 23:00, tổng 73 mốc).
  Giữa hai mốc thì **nội suy tuyến tính ρ**, rồi mới đổi sang (k, v, q). Nhờ vậy `q = k · v` đúng chính xác tại
  mọi t, không chỉ tại các mốc.
- Ngoài cửa sổ mô phỏng thì **giữ giá trị biên** (clamp). Thời gian **không quay vòng theo ngày**: 25:00 dùng
  giá trị lúc 23:00, không dùng giá trị lúc 01:00. Cách này giữ hàm traffic liên tục theo t, nên không phá
  FIFO với các chuyến đi qua nửa đêm.

### Tái lập

`SyntheticProvider(graph, cfg, seed)` (với `seed=None` thì dùng `cfg.seed`) cho **cùng kết quả khi cùng seed**.
Hệ số nhiễu của mỗi edge chỉ phụ thuộc `(seed, edge_id)`, nên thêm hoặc bớt edge không làm đổi traffic của các
edge khác. Điều này được kiểm trong `tests/test_synthetic_provider.py`.

## 4. Effective speed (D5, phần này do P4 cài)

$$
v_{\text{eff}} = v_{free} \cdot \left(1 - \frac{k}{k_{jam}}\right), \text{ giới hạn thêm theo capacity } (q / q_{max})
$$

BPR là mode phụ. Chi tiết và việc đổi đơn vị nằm trong `src/cost/speed_model.py`, là **nơi duy nhất đổi đơn vị**
(km/h sang m/s). Xem thêm §2: với `SyntheticProvider` thì $v_{\text{eff}}$ = `speed_kmh`.

## 5. FIFO

**Điều kiện FIFO:** xuất phát muộn hơn thì không bao giờ tới sớm hơn:

$$
t_1 < t_2 \implies t_1 + c(e, t_1) \le t_2 + c(e, t_2) \quad \forall e
\iff \frac{dc(e, t)}{dt} \ge -1
$$

FIFO là điều kiện để time-dependent Dijkstra và A\* cho kết quả đúng.

- **Bảo đảm bằng thiết kế:** profile Gaussian mượt, nội suy tuyến tính, nhiễu không đổi theo thời gian, clamp
  ngoài cửa sổ (không có bước nhảy).
- **Kiểm bằng test số:** `validation/fifo.py::check_fifo` trả `(edge_id, t1, t2)` của từng vi phạm.
  `fifo_report` trả thêm độ dốc nhỏ nhất và lớn nhất của $c(e, t)$.

Kết quả kiểm (lưới **1 phút** trên cả ngày 00:00 đến 24:00, tức là kiểm cả bên trong ô 15 phút và ngoài cửa sổ):

| Graph | Số edge | Số cặp (t₁, t₂) | Vi phạm | min dc/dt | max dc/dt |
| --- | --- | --- | --- | --- | --- |
| Mock 7 node | 19 | 27 360 | 0 | −0.009 | +0.009 |
| Mọi loại đường × quận, cạnh 500 m | 60 | 86 400 | 0 | −0.008 | +0.008 |
| Mọi loại đường × quận, cạnh 3 km | 60 | 86 400 | 0 | −0.047 | +0.050 |
| Mọi loại đường × quận, cạnh 10 km | 60 | 86 400 | 0 | −0.156 | +0.167 |

Độ dốc âm nhất là −0.156, ứng với cạnh 10 km, dài hơn nhiều so với cạnh giữa hai POI kề nhau. Con số này vẫn còn
rất xa ngưỡng −1. Ngược lại, `MockTrafficProvider` đổi tốc độ đột ngột lúc 09:00 nên **vi phạm** FIFO
(`test_step_traffic_breaks_fifo`). Đây là minh hoạ cho lý do profile phải mượt.

> TODO(P3): chạy lại `fifo_report` trên `data/processed/graph.json` khi WP2 commit graph thật, rồi điền vào bảng.

## 6. SpeedBounds: bảng tốc độ tính trước cho P4

Heuristic cần $V_{ub}(t)$, tức là tốc độ lớn nhất trên **mọi edge** ở **mọi thời điểm ≥ t**. Nếu P4 tự gọi
`get_traffic` thì phải gọi hàng nghìn lần mỗi lần tính heuristic. Vì vậy P3 tính trước **một lần** trong
`traffic/speed_bounds.py` (`compute_speed_bounds(graph, provider, cfg)`):

| Trường / hàm | Định nghĩa | Dùng cho |
| --- | --- | --- |
| `v_max_kmh` | $\max_{e, t} v(e, t)$ | `static_vmax` |
| `v_ub(t)` | $\max_{t' \ge t}\ \max_e v(e, t')$ (suffix max), nội suy giữa các mốc | `dynamic_ub` |
| `v_mean(t)` | Trung bình $v(e, t)$ trên mọi edge | `dynamic_weighted` |
| `network_max_speed(t)` | $\max_e v(e, t)$ tại đúng t (không suffix) | báo cáo, so độ chặt của `v_ub` |

Tham số tuỳ chọn `speed_fn(state, segment) -> km/h` cho phép tính bound theo một tốc độ hiệu dụng khác
`speed_kmh`. Mặc định không cần dùng (xem §2).

**Tính chất bắt buộc của `v_ub`** (kiểm trong `tests/test_speed_bounds.py` trên lưới 5 phút):

1. **Không tăng** theo $t$.
2. $v_{ub}(t) \ge v(e, t')$ với mọi $e$ và mọi $t' \ge t$.

**Chứng minh tính chất 2 giữa hai mốc.** Gọi $M_i = \max_e v(e, t_i)$ và $S_i = \max_{j \ge i} M_j$ (suffix max).
Xét $t = t_i + \lambda h$ với $\lambda \in [0, 1)$.

- Trong một ô lưới, ρ tuyến tính theo t, nên $v(e, \cdot) = \max(v_{min}, \text{tuyến tính})$ là hàm **lồi**.
  Hàm lồi nằm dưới dây cung, nên $v(e, t') \le (1-\lambda')M_i + \lambda' M_{i+1}$.
- Với $t'$ cùng ô và $\lambda' \ge \lambda$: nếu $M_i \le M_{i+1}$ thì vế phải $\le M_{i+1} \le S_{i+1} \le v_{ub}(t)$.
  Nếu $M_i > M_{i+1}$ thì vế phải giảm theo $\lambda'$, nên
  $\le (1-\lambda)M_i + \lambda M_{i+1} \le (1-\lambda)S_i + \lambda S_{i+1} = v_{ub}(t)$.
- Với $t'$ ở các ô sau: $v(e, t') \le \max(M_j, M_{j+1}) \le S_{i+1} \le v_{ub}(t)$.

**Trade-off đã thấy trong số liệu:** với cửa sổ 05:00 đến 23:00, cuối cửa sổ (23:00) thông thoáng, nên
$V_{ub}(t) = v_{max} \approx 38.7$ km/h **gần như hằng** cả ngày. Khi đó `dynamic_ub` ≈ `static_vmax`, đúng như
cảnh báo ở scope §7. Trong khi đó `network_max_speed` giảm xuống ≈ 29.6 km/h lúc 17:30, và `v_mean` giảm từ
27.5 xuống 20.7 km/h. Nếu thu hẹp cửa sổ (ví dụ kết thúc lúc 17:30) thì $V_{ub}$ thực sự giảm theo t
(`test_v_ub_is_time_dependent_when_late_window_is_congested`). Lựa chọn này thuộc phần thí nghiệm, nhóm cần
quyết định.

## 7. Đầu ra cho báo cáo

> TODO(P3):
>
> - Biểu đồ ρ(t), v(t), q(t) cho vài edge tiêu biểu (primary ở Q1, residential ở Bình Thạnh).
> - Biểu đồ `v_ub(t)` so với `network_max_speed(t)` và `v_mean(t)`.
> - Bảng tham số cuối cùng sau khi hiệu chỉnh.
