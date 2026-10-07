# Báo cáo cuối cùng (M9, M10, WP6)

> Owner: **P6** (tổng hợp và thống nhất văn phong). Mỗi người viết phần của WP mình.

## Dàn ý báo cáo PDF

| # | Chương | Nguồn | Người viết |
| --- | --- | --- | --- |
| 1 | Giới thiệu và đề bài | [scope.md](../scope.md) §1–2 | P6 |
| 2 | Phát biểu bài toán và quyết định thiết kế | [scope.md](../scope.md) §3–4 | P6 |
| 3 | Dữ liệu POI | [data_sources.md](../data_sources.md) | P1 |
| 4 | Dựng graph | [graph_construction.md](../graph_construction.md) | P2 |
| 5 | Mô hình giao thông | [traffic_model.md](../traffic_model.md) | P3 |
| 6 | Cost model, heuristic và chứng minh | [heuristic_proof.md](../heuristic_proof.md) | P4 |
| 7 | Thuật toán A\* và giải thích từng bước | [algorithm_walkthrough.md](../algorithm_walkthrough.md) | P5 |
| 8 | Kiểm chứng admissibility và consistency | heuristic_proof §8, algorithm_walkthrough §5 | P5 |
| 9 | Thí nghiệm và kết quả | `outputs/experiments.csv`, `experiments/plots.py` | P6 |
| 10 | Visualization và UI | `viz/`, `cli.py`, `app/` | P6 |
| 11 | Kết luận, hạn chế, hướng phát triển | scope §6–7 | Toàn nhóm |

## Chương 9: thí nghiệm cần có

1. **So sánh 4 heuristic** trên hơn 100 cặp A/B và nhiều giờ xuất phát. Báo cáo theo từng mode:
   - cost trung bình, và tỉ lệ cặp có cost bằng Dijkstra;
   - số expanded nodes trung bình (kèm độ lệch chuẩn);
   - runtime trung bình.
2. **Demo time-dependent:** cùng một cặp A/B, đổi giờ xuất phát (ví dụ 05:00, 07:30, 12:00, 17:30, 22:00).
   Cho thấy cost hoặc route thay đổi, kèm bản đồ các route chồng lên nhau.
3. **`dynamic_ub` so với `static_vmax` theo giờ:** đo độ yếu của suffix max (heuristic_proof §7).
4. **Phản ví dụ `dynamic_weighted`:** bảng các ca vi phạm và một ca vẽ trên bản đồ.

Lệnh tạo số liệu:

```bash
uv run hcmc experiments      # ghi outputs/experiments.csv và các hình
```

> TODO(P6): chèn bảng và hình khi có kết quả.

## Chương 10: UI (D7)

| Tầng | Nội dung | Mức |
| --- | --- | --- |
| T0: CLI | `--start --goal --time --heuristic`; in path, travel time, ETA, expanded nodes, trace | **Bắt buộc** |
| T1: Bản đồ tĩnh | Vẽ POI và route lên bản đồ, xuất HTML | Nên có |
| T2: Interactive | Hiện hơn 100 POI, người dùng chọn 2 điểm và giờ xuất phát, ETA và thống kê hiện bên dưới | Extra |

UI chỉ gọi `Pathfinder` rồi hiển thị `RouteResult`, không chứa logic thuật toán.

> TODO(P6): chụp màn hình CLI, bản đồ T1, và giao diện T2 nếu có.

## Checklist trước khi nộp

- [ ] Đủ 7 sản phẩm bàn giao ([scope.md §9](../scope.md#9-sản-phẩm-bàn-giao)).
- [ ] Đạt mọi tiêu chí hoàn thành ([scope.md §8](../scope.md#8-tiêu-chí-hoàn-thành)).
- [ ] Mọi bản đồ ghi "© OpenStreetMap contributors".
- [ ] Mọi con số trong báo cáo tái lập được bằng `uv run hcmc experiments` với seed trong config.
- [ ] Người trong cặp đã review từng chương.
