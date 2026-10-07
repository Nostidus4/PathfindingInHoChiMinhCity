"""Unit tests cho WP4 edge cost."""

import pytest

from src.cost.edge_cost import edge_cost, make_edge_cost
from src.models import CostMode, RoadSegment, TrafficState
from src.timeutil import parse_hhmm


def _segment() -> RoadSegment:
    return RoadSegment("A->B", "A", "B", 1000.0, "primary")


def test_time_cost_1000m_at_36kmh_is_100s(mock_provider) -> None:
    assert edge_cost(_segment(), parse_hhmm("12:00"), mock_provider) == pytest.approx(100.0)


def test_distance_mode_returns_length_without_querying_provider() -> None:
    class ExplodingProvider:
        def get_traffic(self, edge_id: str, t: float) -> TrafficState:
            raise AssertionError("DISTANCE mode không được query traffic")

    assert edge_cost(_segment(), 0.0, ExplodingProvider(), CostMode.DISTANCE) == 1000.0


def test_rush_hour_increases_time_cost() -> None:
    from src.mocks import MockTrafficProvider

    provider = MockTrafficProvider(speed_kmh=36.0, rush_factor=0.5)
    normal = edge_cost(_segment(), parse_hhmm("12:00"), provider)
    rush = edge_cost(_segment(), parse_hhmm("08:00"), provider)

    assert normal == pytest.approx(100.0)
    assert rush == pytest.approx(200.0)
    assert rush > normal


def test_make_edge_cost_binds_provider(mock_provider) -> None:
    cost_fn = make_edge_cost(mock_provider)
    assert cost_fn(_segment(), parse_hhmm("12:00")) == pytest.approx(100.0)


def test_capacity_penalty_propagates_to_edge_cost() -> None:
    class OverCapacityProvider:
        def get_traffic(self, edge_id: str, t: float) -> TrafficState:
            return TrafficState(20.0, 36.0, 2000.0, capacity_veh_h=1000.0)

    # Capacity penalty reduces 36 -> 18 km/h = 5 m/s, so 1000 m needs 200 s.
    assert edge_cost(_segment(), 0.0, OverCapacityProvider()) == pytest.approx(200.0)


def test_negative_length_is_rejected(mock_provider) -> None:
    segment = RoadSegment("bad", "A", "B", -1.0)
    with pytest.raises(ValueError, match="length_m"):
        edge_cost(segment, 0.0, mock_provider)
