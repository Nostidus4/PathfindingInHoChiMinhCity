"""Hằng số bài toán, trọng số fitness, tham số GA và kịch bản thí nghiệm.  [Gói 1]

Mọi module import hằng số từ đây, KHÔNG tự hard-code lại.
Lưu ý: code xử lý chromosome nên lấy kích thước từ `inst` (vd. len(inst.sec_course),
inst.n_rooms) thay vì N_SECTIONS/N_ROOMS để unit test dùng được instance nhỏ.
"""

# ---------------------------------------------------------------- Bài toán
N_COURSES = 60                 # giả định: đề ghi course_name = {1-50} nhưng 60 × 8 = 480 -> dùng 60 môn
SECTIONS_PER_COURSE = 8
N_SECTIONS = N_COURSES * SECTIONS_PER_COURSE   # 480
SESSIONS_PER_SECTION = 2
N_SESSIONS = N_SECTIONS * SESSIONS_PER_SECTION # 960
N_PROFS = 60
N_DAYS = 5                     # 0..4 = T2..T6
N_SLOTS = 6                    # 0..5 = tiết 1..6
MORNING_SLOTS = (0, 1, 2)      # sáng = tiết 1–3, chiều = tiết 4–6
N_ROOMS_DEFAULT = 20
ROOM_SIZES = (0, 1, 2)         # 0 nhỏ, 1 vừa, 2 lớn
MAX_SECTIONS_PER_PROF = 10
N_FAV_COURSES = 3

DAY_NAMES = ("T2", "T3", "T4", "T5", "T6")

# 6 cặp ngày hợp lệ (không cùng ngày, không liền nhau) -> H2 luôn đúng nhờ mã hóa
DAY_PATTERNS = ((0, 2), (0, 3), (0, 4), (1, 3), (1, 4), (2, 4))

# ---------------------------------------------------------------- Mã hóa gene
# chrom: ndarray int, shape (n_sections, 6); mỗi dòng = 1 section
GENE_PATTERN, GENE_SLOT1, GENE_SLOT2, GENE_ROOM1, GENE_ROOM2, GENE_PROF = range(6)
N_GENE_FIELDS = 6

# ---------------------------------------------------------------- Fitness
# Penalty = W_H * sum(hard) + sum(w_k * soft_k);  Fitness = 1 / (1 + Penalty)
WEIGHTS = {
    "W_H": 1000,   # nhân cho mọi ràng buộc cứng (H1, H3a, H3b, H4, H6, B2 nếu bật)
    "S1": 2,
    "S2": 3,
    "S3": 2,
    "S4": 1,
    "B1": 5,
}
S1_LAMBDA = 1.0          # trọng số phần "số ngày dạy vượt mức" trong S1
B2_IS_HARD = True        # B2 (dạy môn ngoài danh sách) tính như ràng buộc cứng

# ---------------------------------------------------------------- Sinh dữ liệu
DATA_PARAMS = {
    "reg_size_probs": (0.4, 0.4, 0.2),     # tỉ lệ section cỡ 0/1/2 – phải qua kiểm tra khả thi
    "room_size_probs": (0.3, 0.4, 0.3),
    "room_busy_ratio": 0.05,              # tỉ lệ ô (phòng, ngày, tiết) bị bận -> H4 có ý nghĩa
    "can_teach_min": 5,                   # số môn tối thiểu mỗi GV được dạy (Bonus 2)
    "can_teach_max": 10,
}

# ---------------------------------------------------------------- GA
GA_PARAMS = {
    "pop_size": 150,
    "generations": 2000,
    "tournament_k": 3,
    "crossover_rate": 0.9,
    "mutation_genes": (1, 5),     # số gene đột biến mỗi cá thể (min, max)
    "elitism": 3,
    "greedy_init_ratio": 0.10,    # 10% khởi tạo heuristic tham lam
    "use_repair": True,
    "repair_top_ratio": 0.10,     # repair top 10% quần thể
    "conflict_guided_mutation": True,
    "adaptive_window": 50,        # số thế hệ đứng yên trước khi tăng tỉ lệ đột biến
    "stall_generations": 300,     # dừng khi hard = 0 và soft không cải thiện sau ngần này thế hệ
    "log_every": 10,
}

SEED = 42

# ---------------------------------------------------------------- Kịch bản thí nghiệm (main.py)
EXPERIMENTS = {
    "E1": "Đúng đề, 20 phòng – so số trùng phòng với cận dưới 360",
    "E2": "32 / 36 / 40 phòng – chứng minh đạt 0 vi phạm cứng",
    "E3": "Ablation: GA thuần vs +repair vs +repair+đột biến hướng xung đột",
    "E4": "Quét tham số: pop_size, mutation, crossover_rate, tournament_k",
    "E5": "5 seed khác nhau – trung bình ± độ lệch chuẩn",
    "E6": "Có / không có bonus – tỉ lệ GV có môn yêu thích, chi phí đánh đổi",
}
E2_ROOM_COUNTS = (32, 36, 40)
E5_SEEDS = (1, 2, 3, 4, 5)

RESULTS_DIR = "results"
