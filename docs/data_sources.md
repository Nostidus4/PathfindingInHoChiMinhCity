# Dữ liệu POI và nguồn dữ liệu (M2, WP1)

> Owner: **P1** · Review: P2 · Code: `src/data/`, `scripts/build_pois.py`, `scripts/survey_realtime.py`

## 1. Mục tiêu

Tạo dataset khoảng **150 POI** (tối thiểu 100) nằm trong 5 quận trung tâm, **≥ 20 POI mỗi quận**, phân bố
đều, không lệch về một quận. Dataset này đáp ứng R1.

| Quận | Tên trong code | Số POI mục tiêu |
| --- | --- | --- |
| Quận 1 | `Quan 1` | ~30 |
| Quận 3 | `Quan 3` | ~30 |
| Quận 5 | `Quan 5` | ~30 |
| Bình Thạnh | `Binh Thanh` | ~30 |
| Phú Nhuận | `Phu Nhuan` | ~30 |

> Tên quận trong code viết không dấu để tránh lỗi encoding khi đọc/ghi CSV và so khớp chuỗi.

## 2. Định nghĩa POI

Một POI là một điểm mà xe **đi qua được**, thuộc một trong ba loại:

| `kind` | Ý nghĩa | Cách lấy |
| --- | --- | --- |
| `landmark` | Địa điểm nổi tiếng: chợ, bệnh viện, trường, công viên, toà nhà | Lấy tag OSM (`amenity`, `tourism`, `shop=mall`...) rồi snap vào node đường gần nhất |
| `intersection` | Ngã tư, tức node có degree ≥ 3 trên mạng đường | Lấy từ graph đường OSM |
| `junction` | Nút giao lớn, vòng xoay | Tag `junction=roundabout` hoặc chọn tay |

## 3. Định dạng `data/processed/pois.csv`

File này **được commit vào git**, để những người không cài `osmnx` vẫn chạy được.

| Cột | Kiểu | Ví dụ | Ghi chú |
| --- | --- | --- | --- |
| `id` | str | `P001` | Duy nhất |
| `name` | str | `Nguyễn Huệ x Lê Lợi` | Ngã tư đặt tên theo hai đường giao nhau |
| `lat` | float | `10.7731` | WGS84 |
| `lon` | float | `106.7030` | WGS84 |
| `district` | str | `Quan 1` | Một trong 5 quận ở §1 |
| `kind` | str | `intersection` | `landmark` / `intersection` / `junction` |

Các trường này khớp với dataclass `POI` trong `src/models.py`.

## 4. Quy trình dựng dataset

```text
osm_fetch.fetch_road_network()  ──►  data/raw/hcmc_drive.graphml   (cache, không commit)
osm_fetch.fetch_landmarks()     ──►  data/raw/landmarks.geojson
            │
poi_select.select_intersections()  +  poi_select.snap_landmarks()
            │
districts.assign_district()     gán quận, loại điểm nằm ngoài 5 quận
            │
poi_select.balance_by_district()   cân bằng ≥ 20 POI mỗi quận (có seed)
            │
poi_validate.validate_pois()    ──►  báo lỗi nếu không đạt
            │
poi_io.save_pois()              ──►  data/processed/pois.csv       (commit)
preview.render_poi_preview()    ──►  outputs/pois_preview.html
```

Chạy toàn bộ quy trình bằng một lệnh:

```bash
uv sync --group data
uv run python scripts/build_pois.py
```

## 5. Làm sạch và kiểm tra

`poi_validate.validate_pois()` phải trả về danh sách lỗi rỗng:

- [ ] Tổng số POI ≥ 100, mục tiêu khoảng 150.
- [ ] Mỗi quận ≥ 20 POI.
- [ ] Không trùng `id`. Không có hai POI cách nhau dưới `min_sep_m` (mặc định 30 m).
- [ ] Không có toạ độ sai và không có POI nằm ngoài ranh giới 5 quận.
- [ ] Mọi POI nối được vào graph (P2 kiểm lại ở WP2).

> TODO(P1): điền thống kê thật sau khi chạy xong.
>
> | Quận | landmark | intersection | junction | Tổng |
> | --- | --- | --- | --- | --- |
> | Quận 1 | | | | |
> | … | | | | |

## 6. Ranh giới quận

Polygon của 5 quận **do nhóm tự vẽ** và lưu trong `src/data/districts.py`, dạng danh sách `(lat, lon)`.
Hàm `assign_district` dùng thuật toán ray casting viết bằng Python thuần, không cần `shapely`.

> TODO(P1): ghi rõ cách vẽ polygon (công cụ, độ chính xác) và chèn hình preview.

## 7. Nguồn dữ liệu và license

| Nguồn | Dùng cho | License | Cách lấy |
| --- | --- | --- | --- |
| OpenStreetMap | Mạng đường, landmark, tên đường, one-way | ODbL 1.0 | `osmnx` (Overpass API) |
| giaothong.hochiminhcity.gov.vn | (Optional) hiệu chỉnh mức ùn tắc | Chưa rõ, xem §8 | Khảo sát |

Mọi bản đồ và báo cáo phải ghi: **"© OpenStreetMap contributors"**.

> TODO(P1): ghi ngày tải dữ liệu OSM và phiên bản `osmnx`, để người khác tái lập được.

## 8. Khảo sát dữ liệu real-time (R6, optional)

**Time-box: 1–2 ngày, làm sau khi xong dataset.**

Đánh giá ban đầu trong Proposal: cổng giaothong.hochiminhcity.gov.vn có bản đồ giao thông thông minh,
camera, lớp "Tình trạng giao thông" và biển báo tốc độ. Tuy nhiên phần giao diện đọc được **không để lộ API
hay dataset tải về**. Nội dung động không hiển thị, nên chưa xác nhận được có dữ liệu dạng số hay không.

**Việc cần làm:**

1. Mở trang Bản đồ, xem tab Network của trình duyệt xem có endpoint JSON không.
2. Đọc mục Điều khoản sử dụng **trước khi** lấy dữ liệu.
3. Ghi kết luận vào mục dưới đây, **kể cả khi kết quả là "không dùng được"**.

**Cách dùng nếu có dữ liệu:**

- Nếu chỉ có mức ùn tắc dạng nhãn (thông thoáng, đông, kẹt) thì dùng để **hiệu chỉnh ρ**, không thay mô hình.
- Real-time chỉ là snapshot của hiện tại, không cho biết tương lai, nên **không thể** là nguồn duy nhất
  cho bài toán time-dependent.
- Nếu dùng thì phải **đóng băng** dữ liệu ra `data/snapshots/` để test tái lập được. Đọc bằng `RealSnapshotProvider`.

> TODO(P1): kết quả khảo sát
>
> - Ngày khảo sát:
> - Endpoint tìm thấy:
> - Điều khoản:
> - Kết luận: dùng được / không dùng được, vì sao:

## 9. Cặp A/B cho experiment

P1 chọn các cặp (start, goal) **có ý nghĩa thực tế** và điền vào `CURATED_PAIRS` trong
`src/experiments/scenarios.py`. Ngoài ra experiment còn chạy trên hơn 100 cặp ngẫu nhiên.

Tiêu chí chọn:

- Có cặp đi xuyên quận (ví dụ Quận 5 → Bình Thạnh).
- Có cặp đi qua khu vực hay kẹt giờ cao điểm (Quận 1, Quận 3).
- Có ít nhất một cặp mà đổi giờ xuất phát thì **route thay đổi**, không chỉ cost thay đổi (tiêu chí hoàn thành).

> TODO(P1): liệt kê các cặp đã chọn và lý do.
