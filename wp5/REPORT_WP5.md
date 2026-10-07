# Ghi chú báo cáo WP5 — M7/M8

WP5 xây dựng engine tìm đường có chi phí phụ thuộc thời điểm đi vào cạnh và bộ kiểm chứng heuristic.
Engine nhận graph, edge_cost và heuristic qua tham số, không phụ thuộc UI, mạng hay nguồn traffic.

A* duy trì priority queue theo f = g + h. Khi expand u, thời điểm đi vào cạnh là t0 + g(u).
Mỗi relaxation dùng c(u,v,t0+g(u)), sau đó tính heuristic tại thời điểm đến v.
Khi cải thiện g, engine tạo label mới; entry cũ bị bỏ qua khi pop.
Tie breaker số thứ tự tránh so sánh node ID. Node đã expand được mở lại nếu label mới tốt hơn.
Các parent label bất biến giúp tái dựng đúng đường và cạnh của label đến goal.
Dijkstra có triển khai riêng và dùng cùng mô hình cost để đối chiếu.

Optimality của hai thuật toán dựa trên giả định FIFO và chi phí không âm.
FIFO làm cho thời điểm đến sớm hơn không dẫn đến thời điểm tới cuối cạnh muộn hơn,
nên một earliest-arrival label trên mỗi node đủ cho bài toán không có hành động chờ.
A* cần heuristic admissible và h(goal,t)=0; weighted heuristic không có bảo đảm này.

Admissibility validator so h(n,goal,t) với travel time của Dijkstra từ n tại t.
Consistency validator kiểm tra h(u,t) <= c(u,v,t) + h(v,t+c).
FIFO validator so arrival t+c(e,t) ở các departure liên tiếp trên lưới đã chọn.
Optimality validator lưu cặp route/cost A* và Dijkstra khi sai lệch vượt tolerance.

Trên fixture synthetic 6 node, 17 unit tests PASS. Bộ all-pairs kiểm tra 10.476 phép so sánh
(36 cặp × 97 thời điểm × 3 mode). Ba heuristic zero/static_vmax/dynamic_ub qua các validator mẫu.
Dynamic_weighted với w=4 vi phạm admissibility/consistency và chọn đường trực tiếp S→G,
trong khi oracle chọn S→A→G với travel time nhỏ hơn. JSON chứa counterexample cụ thể.
Traffic tăng travel time theo departure, giúp kiểm tra mô hình time-dependent.

Những số liệu này chỉ thể hiện WP5 trên mock. Khi tích hợp, nhóm phải chạy lại trên dataset thực
>=100 POI và traffic WP3/WP4. Sample PASS không thay thế chứng minh toán và không chứng minh FIFO
trên toàn miền liên tục. Các kết quả expanded_nodes/runtime phải đo trên graph thực, không giả định
A* luôn nhanh hơn hoặc expand ít node hơn Dijkstra.

Bộ nhớ khi trace tắt chủ yếu là labels và heap; heap có thể chứa entries stale.
Với heuristic inconsistent, một node có thể được reopen nhiều lần, nên không áp dụng máy móc
bound label-setting O((V+E)log V). Trace bật có thêm snapshot open set mỗi expansion,
làm tăng bộ nhớ và thời gian; chỉ dùng cho giải thích/demo.
