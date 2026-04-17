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

    def step(self, width: int, height: int, rng: random.Random) -> None:
        """Move using the local forward choices and spend one unit of energy."""
        if not self.alive:
            return

        chosen_direction = self._choose_direction(width=width, height=height, rng=rng)
        if chosen_direction is not None:
            dx, dy = DIRECTION_OFFSETS[chosen_direction]
            self.x += dx
            self.y += dy
            self.direction = chosen_direction
        else:
            # Turn around when fully blocked so the ant can leave the edge next tick.
            self.direction = (self.direction + 4) % len(DIRECTION_OFFSETS)

        # A blocked ant still spends the tick attempting to move.
        self.energy -= MOVE_COST
        if self.energy <= 0:
            self.alive = False

    def _choose_direction(self, width: int, height: int, rng: random.Random) -> int | None:
        """Pick a valid direction from forward-left, forward, and forward-right."""
        directions = [
            (self.direction - 1) % len(DIRECTION_OFFSETS),
            self.direction,
            (self.direction + 1) % len(DIRECTION_OFFSETS),
        ]
        rng.shuffle(directions)

        for direction in directions:
            dx, dy = DIRECTION_OFFSETS[direction]
            new_x = self.x + dx
            new_y = self.y + dy

            if 0 <= new_x < width and 0 <= new_y < height:
                return direction

        return None
