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
| `landmark` | Địa điểm nổi tiếng: chợ, bệnh viện, trường, công viên, toà nhà | Lấy tag OSM (`amenity`, `tourism`, `shop=mall`...), xếp hạng (có `wikidata` → loại → diện tích), mỗi quận 4 landmark khác loại, snap vào node đường gần nhất |
| `intersection` | Ngã tư thật trên đường chính (tiêu chí ở §5) | Lấy từ graph đường OSM |
| `junction` | Nút giao lớn, vòng xoay | Tag `junction=roundabout` hoặc chọn tay |

## 3. Định dạng `data/processed/pois.csv`

File này **được commit vào git**, để những người không cài `osmnx` vẫn chạy được.

| Cột | Kiểu | Ví dụ | Ghi chú |
| --- | --- | --- | --- |
| `id` | str | `2493366320`, `Lw39514795` | Duy nhất. Ngã tư: id node OSM. Landmark: `L` + loại phần tử OSM (`n`/`w`/`r`) + id OSM |
| `name` | str | `Nguyễn Huệ x Lê Lợi` | Ngã tư đặt tên theo hai đường giao nhau |
| `lat` | float | `10.7731` | WGS84 |
| `lon` | float | `106.7030` | WGS84 |
| `district` | str | `Quan 1` | Một trong 5 quận ở §1 |
| `kind` | str | `intersection` | `landmark` / `intersection` / `junction` |

Các trường này khớp với dataclass `POI` trong `src/models.py`.

## 4. Quy trình dựng dataset

```text
scripts/extract_districts.py    ──►  src/data/district_polygons.py (ranh giới thật, commit, §6)
osm_fetch.fetch_road_network()  ──►  data/raw/hcmc_drive.graphml   (cache, không commit; vùng 5 quận + 1 km)
osm_fetch.fetch_landmarks()     ──►  data/raw/landmarks.geojson    (cache, không commit)
            │
poi_select.select_intersections()  +  poi_select.snap_landmarks()
            │                    (chỉ node thuộc thành phần liên thông mạnh lớn nhất của mạng OSM)
districts.assign_district()     gán quận, loại điểm ngoài 5 quận hoặc cách ranh giới < 20 m
            │
poi_select.balance_by_district()   30 POI mỗi quận: landmark trước, rồi farthest-point sampling
            │
poi_validate.validate_pois()    ──►  báo lỗi nếu không đạt
            │
poi_io.save_pois()              ──►  data/processed/pois.csv       (commit)
preview.render_poi_preview()    ──►  outputs/pois_preview.html
```

Chạy toàn bộ quy trình bằng một lệnh:

```bash
uv sync --group data
uv run python scripts/build_pois.py           # --per-district 30 --landmarks-per-district 4 --min-sep-m 150
uv run python scripts/extract_districts.py    # chỉ khi cần tải lại ranh giới quận (§6)
```

## 5. Làm sạch và kiểm tra

`poi_validate.validate_pois()` phải trả về danh sách lỗi rỗng:

- [x] Tổng số POI ≥ 100, mục tiêu khoảng 150.
- [x] Mỗi quận ≥ 20 POI.
- [x] Không trùng `id`. Không có hai POI cách nhau dưới `min_sep_m` (`build_pois.py` dùng 150 m).
- [x] Không có toạ độ sai và không có POI nằm ngoài ranh giới 5 quận.
- [x] Nhãn `district` khớp với polygon của quận đó (trước đây chỉ kiểm "nằm trong một quận nào đó").
- [x] Mọi POI nối được vào graph: chỉ chọn node thuộc thành phần liên thông mạnh lớn nhất của mạng OSM
  (P2 kiểm lại ở WP2).

**Tiêu chí chọn ngã tư** (`select_intersections`): `street_count` ≥ 3 (số con đường vật lý gặp nhau, không
dùng degree của đồ thị có hướng vì đường hai chiều bị đếm hai lần), có ít nhất một đường chính
(`trunk`/`primary`/`secondary`/`tertiary`), ít nhất hai đường có tên không phải hẻm, và cách ranh giới quận
≥ 20 m (lớn hơn sai số polygon, nên nhãn quận chắc chắn đúng).

**Thống kê** (chạy ngày 08/10/2026, `seed = 42`):

| Quận | landmark | intersection | junction | Tổng |
| --- | --- | --- | --- | --- |
| Quận 1 | 4 | 26 | 0 | 30 |
| Quận 3 | 4 | 26 | 0 | 30 |
| Quận 5 | 4 | 26 | 0 | 30 |
| Bình Thạnh | 4 | 26 | 0 | 30 |
| Phú Nhuận | 4 | 26 | 0 | 30 |
| **Tổng** | **20** | **130** | **0** | **150** |

- Ứng viên ngã tư đạt tiêu chí: 1 147 (Quận 1: 390, Quận 3: 137, Quận 5: 284, Bình Thạnh: 234, Phú Nhuận: 102).
- Khoảng cách tới POI gần nhất: nhỏ nhất 232 m, trung vị 370 m, lớn nhất 742 m.
- Landmark: Chợ Bến Thành, Bảo tàng Mỹ thuật, Chợ Dân Sinh, Thảo Cầm Viên (Quận 1); Bảo tàng Chứng tích
  Chiến tranh, Bệnh viện Mắt, Đại học Kiến trúc, Chùa Vĩnh Nghiêm (Quận 3); Bệnh viện Chợ Rẫy, Đại học Sài
  Gòn, THPT chuyên Lê Hồng Phong, Chợ An Đông (Quận 5); Bệnh viện Nhân dân Gia Định, THPT Gia Định, Chợ Bà
  Chiểu, Vân Đường Phủ (Bình Thạnh); Viện Y Dược học Dân tộc, Chợ Trần Hữu Trang, Học viện Hàng không Việt
  Nam, Đài tưởng niệm liệt sỹ Phú Nhuận (Phú Nhuận). Mỗi landmark nằm cách hình thật của nó 0–54 m.
- Loại `junction` chưa dùng: vòng xoay lớn đã có trong tập ngã tư (ví dụ Công trường Quách Thị Trang).

## 6. Ranh giới quận

Polygon của 5 quận là **ranh giới thật lấy từ OpenStreetMap**, lưu trong `src/data/district_polygons.py`
(file sinh tự động) dạng danh sách `(lat, lon)`; `src/data/districts.py` dùng lại. Hàm `assign_district` dùng
thuật toán ray casting viết bằng Python thuần, không cần `shapely`.

- **Nguồn:** từ 01/07/2025 TP.HCM bỏ cấp quận, nhưng OSM vẫn giữ ranh giới cũ dưới dạng relation
  `boundary=historic` (`end_date=2025-06-30`): Quận 1 `2587287`, Quận 3 `3819816`, Quận 5 `3820432`,
  Bình Thạnh `3797166`, Phú Nhuận `3851694`.
- **Cách sinh:** `uv run python scripts/extract_districts.py` tải các relation qua Overpass, lấy phần đa giác
  lớn nhất, đơn giản hoá với sai số 10 m (Quận 1: 53 đỉnh, Quận 3: 42, Quận 5: 28, Bình Thạnh: 169,
  Phú Nhuận: 115).
- **Độ chính xác:** so với polygon gốc trên 9 911 node đường, `assign_district` khớp 99,47%; mọi điểm lệch
  đều nằm trong 5,6 m quanh ranh giới. Vì vậy POI phải cách ranh giới ≥ 20 m (§5).
- **Vì sao bỏ bản vẽ tay:** bản cũ là 5 hình chữ nhật chồng lên nhau và lấn sang quận khác; khi đối chiếu
  với ranh giới thật, 83/150 POI cũ nằm sai quận hoặc ngoài 5 quận (Tân Bình, Gò Vấp, Quận 10, 11, 8, 4,
  Thủ Đức).

Preview: `outputs/pois_preview.html` (vẽ polygon quận và POI tô màu theo quận).

## 7. Nguồn dữ liệu và license

| Nguồn | Dùng cho | License | Cách lấy |
| --- | --- | --- | --- |
| OpenStreetMap | Mạng đường, landmark, tên đường, one-way | ODbL 1.0 | `osmnx` (Overpass API) |
| giaothong.hochiminhcity.gov.vn | (Optional) hiệu chỉnh mức ùn tắc | Chưa rõ, xem §8 | Khảo sát |

Mọi bản đồ và báo cáo phải ghi: **"© OpenStreetMap contributors"**.

**Tái lập:** dữ liệu OSM tải ngày 08/10/2026 bằng `osmnx` 2.1.1 (Overpass API). Mạng đường: 20 233 node,
46 743 cạnh; landmark: 1 571 đối tượng. OSM thay đổi liên tục, nên chạy lại sau ngày này có thể ra tập POI
hơi khác; `pois.csv` đã commit là bản chuẩn của nhóm.

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
