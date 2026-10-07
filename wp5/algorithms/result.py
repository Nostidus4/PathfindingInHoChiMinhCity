"""Public result objects. All times are seconds; distances are metres."""
from collections.abc import Hashable
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class RouteResult:
    path: list[Hashable]
    departure_time: float
    estimated_arrival_time: float
    total_travel_time: float
    total_distance: float
    expanded_nodes: int
    execution_time: float
    trace: list[dict[str, Any]] | None = None
    edge_ids: list[Hashable] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
