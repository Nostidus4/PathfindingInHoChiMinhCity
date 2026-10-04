"""WP3 - Traffic Data Layer (owner: P3, review: P4).

Cung cấp TrafficProvider (synthetic / snapshot) và SpeedBounds cho heuristic.

    WP3.1 contract      : models.TrafficState, models.TrafficProvider, base.BaseTrafficProvider,
                          config.SimConfig (tham số)
    WP3.2 profile rho   : profiles.py (daily_profile, road_type_factor, area_factor, density_ratio)
    WP3.3 Greenshields  : greenshields.py (hàm thuần), synthetic.SyntheticProvider.get_traffic
    WP3.4 thời gian     : timeslots.TimeGrid (normalize_time, get_time_slot, interpolate),
                          speed_bounds.SpeedBounds (v_ub, v_mean, network_max_speed)
    WP3.5 validation    : checks.check_traffic_states, validation/fifo.py (check_fifo, fifo_report)
"""
