from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

import numpy as np
import numpy.typing as npt
import pygame

from sim.config import CELL_SIZE, COLOR_EMPTY, COLOR_FOOD, COLOR_NEST
from sim.world import FOOD, NEST

COLOR_ANT = (240, 240, 240)
COLOR_ANT_CARRYING = (240, 220, 70)
COLOR_OVERLAY_TEXT = (240, 240, 240)
COLOR_OVERLAY_BACKGROUND = (10, 10, 10)


class WorldView(Protocol):
    """Describe the world data the renderer needs in order to draw it."""

    width: int
    height: int
    cell_type: npt.NDArray[np.int_]


class AntView(Protocol):
    """Describe the ant state the renderer needs in order to draw markers."""

    x: int
    y: int
    carrying_food: bool
    alive: bool


@dataclass
class OverlayState:
    """Group the small status values shown in the corner overlay."""

    tick: int
    living_ants: int
    delivered_food: int
    ants_carrying_food: int
    remaining_total_food: int
    paused: bool


class Renderer:
    def __init__(self, world: WorldView) -> None:
        """Store renderer defaults and bind the initial world."""
        self.cell_size: int = CELL_SIZE
        self.font = pygame.font.Font(None, 24)
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

    def draw_ants(self, surface: pygame.Surface, ants: Sequence[AntView]) -> None:
        """Draw each living ant as a small marker centered inside its cell."""
        ant_size = max(4, self.cell_size // 2)

        for ant in ants:
            if not ant.alive:
                continue

            color = COLOR_ANT_CARRYING if ant.carrying_food else COLOR_ANT
            rect = pygame.Rect(
                ant.x * self.cell_size + (self.cell_size - ant_size) // 2,
                ant.y * self.cell_size + (self.cell_size - ant_size) // 2,
                ant_size,
                ant_size,
            )
            surface.fill(color, rect)

    def draw_overlay(self, surface: pygame.Surface, overlay: OverlayState) -> None:
        """Render a small text overlay with the current simulation status."""
        status = "Paused" if overlay.paused else "Running"
        lines = [
            f"Tick: {overlay.tick}",
            f"Living ants: {overlay.living_ants}",
            f"Delivered food: {overlay.delivered_food}",
            f"Carrying food: {overlay.ants_carrying_food}",
            f"Remaining food: {overlay.remaining_total_food}",
            f"State: {status}",
        ]
        line_surfaces = [self.font.render(line, True, COLOR_OVERLAY_TEXT) for line in lines]
        text_width = max(line_surface.get_width() for line_surface in line_surfaces)
        text_height = sum(line_surface.get_height() for line_surface in line_surfaces)
        padding = 8
        background = pygame.Rect(
            padding,
            padding,
            text_width + padding * 2,
            text_height + padding * 2,
        )

        surface.fill(COLOR_OVERLAY_BACKGROUND, background)

        y = background.top + padding
        for line_surface in line_surfaces:
            surface.blit(line_surface, (background.left + padding, y))
            y += line_surface.get_height()
