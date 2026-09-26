# Tài liệu dự án

Toàn bộ tài liệu dựa trên *Scope Proposal — Topic 2: Pathfinding in Ho Chi Minh City*.
Mỗi người viết tài liệu cho WP của mình, người trong cặp review, P6 tổng hợp vào báo cáo.

| File | Owner | Module | Nội dung |
| --- | --- | --- | --- |
| [scope.md](scope.md) | Toàn nhóm | M1 | Đề bài, yêu cầu R1–R6, phát biểu bài toán, quyết định thiết kế D1–D8, phạm vi, rủi ro, tiêu chí hoàn thành |
| [data_sources.md](data_sources.md) | P1 | M2 | Dữ liệu POI, nguồn OSM, license, khảo sát real-time |
| [graph_construction.md](graph_construction.md) | P2 | M3 | Cách dựng graph POI từ OSM, định dạng file, các kiểm tra |
| [traffic_model.md](traffic_model.md) | P3 | M4 | Mô hình Greenshields, profile theo giờ, FIFO, SpeedBounds |
| [heuristic_proof.md](heuristic_proof.md) | P4 | M5, M6 | Edge cost, 4 heuristic, chứng minh admissible và consistent |
| [algorithm_walkthrough.md](algorithm_walkthrough.md) | P5 | M7, M8 | Time-dependent A\*, Dijkstra, trace, validation |
| [report/](report/README.md) | P6 | M9, M10 | Dàn ý báo cáo PDF cuối cùng |

**Quy ước khi viết:**

- Ký hiệu toán thống nhất với [scope.md §3](scope.md#3-phát-biểu-bài-toán).
- Đơn vị: thời gian tính bằng giây, chiều dài tính bằng mét, tốc độ trong `TrafficState` tính bằng km/h.
- Chỗ nào còn chờ số liệu thật thì đánh dấu `> TODO(Px): ...` để dễ tìm.
- Hình và bảng xuất từ code nằm trong `outputs/`. Chỉ chép vào `docs/report/` khi chốt báo cáo.
