from __future__ import annotations

import random
from dataclasses import dataclass

from sim.config import MAX_ENERGY, MOVE_COST

Coordinate = tuple[int, int]

# Directions are stored in clockwise order so turning left or right is a +/- 1 step.
DIRECTION_OFFSETS: tuple[Coordinate, ...] = (
    (0, -1),
    (1, -1),
    (1, 0),
    (1, 1),
    (0, 1),
    (-1, 1),
    (-1, 0),
    (-1, -1),
)


@dataclass
class Ant:
    """Store the minimal per-ant state needed for the current step."""

    x: int
    y: int
    direction: int
    energy: int = MAX_ENERGY
    carrying_food: bool = False
    alive: bool = True

    def reverse_direction(self) -> None:
        """Turn the ant around by 180 degrees."""
        self.direction = (self.direction + 4) % len(DIRECTION_OFFSETS)

    def step(
        self,
        width: int,
        height: int,
        rng: random.Random,
        forced_direction: int | None = None,
    ) -> None:
        """Move using the local forward choices and spend one unit of energy."""
        if not self.alive:
            return

        chosen_direction = self._choose_direction(
            width=width,
            height=height,
            rng=rng,
            forced_direction=forced_direction,
        )
        if chosen_direction is not None:
            dx, dy = DIRECTION_OFFSETS[chosen_direction]
            self.x += dx
            self.y += dy
            self.direction = chosen_direction
        else:
            # Turn around when fully blocked so the ant can leave the edge next tick.
            self.reverse_direction()

        # A blocked ant still spends the tick attempting to move.
        self.energy -= MOVE_COST
        if self.energy <= 0:
            self.alive = False

    def candidate_directions(self) -> list[int]:
        """Return the forward-left, forward, and forward-right directions."""
        return [
            (self.direction - 1) % len(DIRECTION_OFFSETS),
            self.direction,
            (self.direction + 1) % len(DIRECTION_OFFSETS),
        ]

    def _choose_direction(
        self,
        width: int,
        height: int,
        rng: random.Random,
        forced_direction: int | None = None,
    ) -> int | None:
        """Pick a valid direction from forward-left, forward, and forward-right."""
        if forced_direction is not None and self._is_valid_direction(forced_direction, width=width, height=height):
            return forced_direction

        directions = self.candidate_directions()
        rng.shuffle(directions)

        for direction in directions:
            if self._is_valid_direction(direction, width=width, height=height):
                return direction

        return None

    def _is_valid_direction(self, direction: int, width: int, height: int) -> bool:
        """Return whether a one-step move in this direction stays inside the grid."""
        dx, dy = DIRECTION_OFFSETS[direction]
        new_x = self.x + dx
        new_y = self.y + dy
        return 0 <= new_x < width and 0 <= new_y < height
