from __future__ import annotations

from typing import Protocol

import numpy as np
import numpy.typing as npt
import pygame

from sim.config import CELL_SIZE, COLOR_EMPTY, COLOR_FOOD, COLOR_NEST
from sim.world import FOOD, NEST


class WorldView(Protocol):
    """Describe the world data the renderer needs in order to draw it."""

    width: int
    height: int
    cell_type: npt.NDArray[np.int_]


class Renderer:
    def __init__(self, world: WorldView) -> None:
        """Store renderer defaults and bind the initial world."""
        self.cell_size: int = CELL_SIZE
        self.world: WorldView
        self.width: int
        self.height: int
        self.set_world(world)

    def set_world(self, world: WorldView) -> None:
        """Attach a world and recompute the pixel dimensions of the window."""
        self.world = world
        self.width = world.width * self.cell_size
        self.height = world.height * self.cell_size

    def draw(self, surface: pygame.Surface) -> None:
        """Paint each world cell as a solid rectangle based on its cell type."""
        for y in range(self.world.height):
            for x in range(self.world.width):
                cell = int(self.world.cell_type[y, x])

                if cell == NEST:
                    color = COLOR_NEST
                elif cell == FOOD:
                    color = COLOR_FOOD
                else:
                    color = COLOR_EMPTY

                rect = pygame.Rect(
                    x * self.cell_size,
                    y * self.cell_size,
                    self.cell_size,
                    self.cell_size,
                )
                surface.fill(color, rect)
