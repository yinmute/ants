from __future__ import annotations

import random
from typing import Optional

import numpy as np
import numpy.typing as npt

from sim.config import (
    DEPOSIT_FOOD,
    DEPOSIT_HOME,
    FOOD_PATCH_COUNT,
    FOOD_PER_PATCH,
    FOOD_PHEROMONE_DECAY,
    GRID_HEIGHT,
    GRID_WIDTH,
    HOME_PHEROMONE_DECAY,
    NEST_SIZE,
    PHEROMONE_MAX,
    PHEROMONE_MIN_CLAMP,
)

EMPTY = 0
NEST = 1
FOOD = 2

GridInt = npt.NDArray[np.int_]
GridFloat = npt.NDArray[np.float64]
Coordinate = tuple[int, int]
Quadrant = tuple[int, int, int, int]


class World:
    def __init__(self, seed: Optional[int] = None) -> None:
        """Build a world instance and immediately populate its grid state."""
        self.width: int = GRID_WIDTH
        self.height: int = GRID_HEIGHT
        self.random: random.Random = random.Random()
        self.cell_type: GridInt
        self.food_amount: GridInt
        self.home_pheromone: GridFloat
        self.food_pheromone: GridFloat
        self.reset(seed=seed)

    def reset(self, seed: Optional[int] = None) -> None:
        """Clear all arrays and recreate the nest and food layout."""
        self.random = random.Random(seed)

        # Core grid state for the simulation.
        self.cell_type = np.zeros((self.height, self.width), dtype=int)
        self.food_amount = np.zeros((self.height, self.width), dtype=int)
        self.home_pheromone = np.zeros((self.height, self.width), dtype=float)
        self.food_pheromone = np.zeros((self.height, self.width), dtype=float)

        self._place_nest()
        self._place_food()

    def nest_cells(self) -> list[Coordinate]:
        """Return all nest cell coordinates as (x, y) pairs."""
        ys, xs = np.where(self.cell_type == NEST)
        return list(zip(xs.tolist(), ys.tolist()))

    def total_food(self) -> int:
        """Sum all food units currently stored in the grid."""
        return int(self.food_amount.sum())

    def evaporate_pheromones(self) -> None:
        """Decay both pheromone layers and clear out tiny residual values."""
        self.home_pheromone *= HOME_PHEROMONE_DECAY
        self.food_pheromone *= FOOD_PHEROMONE_DECAY

        self.home_pheromone[self.home_pheromone < PHEROMONE_MIN_CLAMP] = 0.0
        self.food_pheromone[self.food_pheromone < PHEROMONE_MIN_CLAMP] = 0.0

    def deposit_home_pheromone(self, x: int, y: int, amount: float = DEPOSIT_HOME) -> None:
        """Add home pheromone to the given cell."""
        self.home_pheromone[y, x] = min(PHEROMONE_MAX, self.home_pheromone[y, x] + amount)

    def deposit_food_pheromone(self, x: int, y: int) -> None:
        """Add one unit of food pheromone to the given cell."""
        self.food_pheromone[y, x] = min(PHEROMONE_MAX, self.food_pheromone[y, x] + DEPOSIT_FOOD)

    def consume_food(self, x: int, y: int) -> bool:
        """Remove one food unit from a cell and clear it when depleted."""
        if self.food_amount[y, x] <= 0:
            return False

        self.food_amount[y, x] -= 1
        if self.food_amount[y, x] == 0:
            self.cell_type[y, x] = EMPTY

        return True

    def _place_nest(self) -> None:
        """Mark the centered 3x3 nest area in the cell type grid."""
        start_x = self.width // 2 - NEST_SIZE // 2
        start_y = self.height // 2 - NEST_SIZE // 2
        # The nest is a fixed 3x3 block in the center.
        self.cell_type[start_y:start_y + NEST_SIZE, start_x:start_x + NEST_SIZE] = NEST

    def _place_food(self) -> None:
        """Create three food patches in different quadrants away from the nest."""
        center_x = self.width // 2
        center_y = self.height // 2
        margin = 6
        patch_size = 3

        quadrants: list[Quadrant] = [
            (margin, center_x - margin - patch_size, margin, center_y - margin - patch_size),
            (center_x + margin, self.width - margin - patch_size, margin, center_y - margin - patch_size),
            (margin, center_x - margin - patch_size, center_y + margin, self.height - margin - patch_size),
            (center_x + margin, self.width - margin - patch_size, center_y + margin, self.height - margin - patch_size),
        ]

        # Choose three different quadrants so food starts spread around the world.
        for x_min, x_max, y_min, y_max in self.random.sample(quadrants, FOOD_PATCH_COUNT):
            x = self.random.randint(x_min, x_max)
            y = self.random.randint(y_min, y_max)

            cells: list[Coordinate] = [(px, py) for py in range(y, y + patch_size) for px in range(x, x + patch_size)]
            remaining: int = FOOD_PER_PATCH

            for index, (px, py) in enumerate(cells):
                # Split the patch total across its 3x3 cells without losing units.
                cell_food: int = remaining // (len(cells) - index)
                self.cell_type[py, px] = FOOD
                self.food_amount[py, px] = cell_food
                remaining -= cell_food
