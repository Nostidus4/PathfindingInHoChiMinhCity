"""Unit tests cho WP4 speed model."""

import math

import pytest

from src.cost.speed_model import effective_speed, kmh_to_ms
from src.models import RoadSegment, TrafficState


@pytest.fixture
def segment() -> RoadSegment:
    return RoadSegment("A->B", "A", "B", 1000.0, "primary")


def test_kmh_to_ms_36_is_10() -> None:
    assert kmh_to_ms(36.0) == pytest.approx(10.0)


def test_effective_speed_uses_provider_speed_when_below_capacity(segment: RoadSegment) -> None:
    state = TrafficState(
        density_veh_km=20.0,
        speed_kmh=36.0,
        flow_veh_h=720.0,
        capacity_veh_h=1000.0,
    )
    assert effective_speed(state, segment) == pytest.approx(10.0)


def test_effective_speed_is_capacity_limited(segment: RoadSegment) -> None:
    state = TrafficState(
        density_veh_km=20.0,
        speed_kmh=36.0,
        flow_veh_h=2000.0,
        capacity_veh_h=1000.0,
    )

    # flow gấp đôi capacity -> tốc độ còn một nửa: 18 km/h = 5 m/s.
    assert effective_speed(state, segment) == pytest.approx(5.0)


def test_infinite_capacity_does_not_penalize_speed(segment: RoadSegment) -> None:
    state = TrafficState(20.0, 36.0, 10_000.0, capacity_veh_h=math.inf)
    assert effective_speed(state, segment) == pytest.approx(10.0)


def test_effective_speed_is_always_positive(segment: RoadSegment) -> None:
    state = TrafficState(150.0, 0.0, 0.0, capacity_veh_h=0.0)
    assert effective_speed(state, segment) > 0.0
