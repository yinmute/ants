import unittest

import numpy as np
import numpy.typing as npt
import pygame

from sim.config import CELL_SIZE, COLOR_EMPTY, COLOR_FOOD, COLOR_NEST
from sim.render import COLOR_ANT, COLOR_ANT_CARRYING, OverlayState, Renderer
from sim.world import FOOD, NEST


class FakeWorld:
    def __init__(self, width: int, height: int) -> None:
        """Build a minimal world-shaped object for renderer unit tests."""
        self.width = width
        self.height = height
        self.cell_type: npt.NDArray[np.int_] = np.zeros((height, width), dtype=int)


class FakeAnt:
    def __init__(self, x: int, y: int, carrying_food: bool = False, alive: bool = True) -> None:
        """Build a minimal ant-shaped object for renderer unit tests."""
        self.x = x
        self.y = y
        self.carrying_food = carrying_food
        self.alive = alive


class RendererTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Initialize pygame once so surfaces can be created in the tests."""
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        """Shut down pygame after all renderer tests have finished."""
        pygame.quit()

    def test_renderer_uses_world_dimensions(self) -> None:
        """Renderer size should match the world dimensions times cell size."""
        world = FakeWorld(width=64, height=64)

        renderer = Renderer(world)

        self.assertEqual(renderer.cell_size, CELL_SIZE)
        self.assertEqual(renderer.width, 64 * CELL_SIZE)
        self.assertEqual(renderer.height, 64 * CELL_SIZE)

    def test_set_world_recomputes_render_size(self) -> None:
        """Changing the world should update the renderer's cached size."""
        initial_world = FakeWorld(width=64, height=64)
        updated_world = FakeWorld(width=8, height=5)
        renderer = Renderer(initial_world)

        renderer.set_world(updated_world)

        self.assertIs(renderer.world, updated_world)
        self.assertEqual(renderer.width, 8 * CELL_SIZE)
        self.assertEqual(renderer.height, 5 * CELL_SIZE)

    def test_draw_paints_empty_nest_and_food_cells(self) -> None:
        """Drawing should fill each cell rectangle with the expected color."""
        world = FakeWorld(width=3, height=2)
        world.cell_type[0, 1] = NEST
        world.cell_type[1, 2] = FOOD
        renderer = Renderer(world)
        surface = pygame.Surface((renderer.width, renderer.height))
        surface.fill((255, 0, 255))

        renderer.draw(surface)

        self.assertEqual(surface.get_at((5, 5))[:3], COLOR_EMPTY)
        self.assertEqual(surface.get_at((15, 5))[:3], COLOR_NEST)
        self.assertEqual(surface.get_at((25, 15))[:3], COLOR_FOOD)

    def test_draw_ants_paints_living_ant_markers(self) -> None:
        """Living ants should be drawn on top of the world with the expected colors."""
        world = FakeWorld(width=3, height=2)
        renderer = Renderer(world)
        surface = pygame.Surface((renderer.width, renderer.height))
        ants = [
            FakeAnt(x=0, y=0),
            FakeAnt(x=1, y=0, carrying_food=True),
            FakeAnt(x=2, y=0, alive=False),
        ]

        renderer.draw(surface)
        renderer.draw_ants(surface, ants)

        self.assertEqual(surface.get_at((5, 5))[:3], COLOR_ANT)
        self.assertEqual(surface.get_at((15, 5))[:3], COLOR_ANT_CARRYING)
        self.assertEqual(surface.get_at((25, 5))[:3], COLOR_EMPTY)

    def test_draw_overlay_adds_visible_text_block(self) -> None:
        """The overlay should draw a status block in the top-left corner."""
        world = FakeWorld(width=3, height=2)
        renderer = Renderer(world)
        surface = pygame.Surface((renderer.width, renderer.height))
        surface.fill(COLOR_EMPTY)

        renderer.draw_overlay(
            surface,
            OverlayState(
                tick=12,
                living_ants=7,
                delivered_food=2,
                ants_carrying_food=3,
                remaining_total_food=120,
                paused=True,
            ),
        )

        self.assertNotEqual(surface.get_at((8, 8))[:3], COLOR_EMPTY)


if __name__ == "__main__":
    unittest.main()
