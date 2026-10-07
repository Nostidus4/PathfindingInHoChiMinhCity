"""src: Time-Dependent Traffic-Aware A* cho TOPIC 2 (Pathfinding in HCMC).

Quy tắc phụ thuộc (mỗi tầng chỉ import tầng bên dưới):

    models/geo/timeutil/config -> data -> graph -> traffic -> cost -> search -> validation
                                                                          |
                                                    experiments / viz / cli / app

search/ KHÔNG được import viz, cli, osmnx hay streamlit (A* không phụ thuộc UI/API).
"""

__version__ = "0.1.0"
