import unittest

from sim.config import (
    FOOD_PATCH_COUNT,
    FOOD_PER_PATCH,
    FOOD_PHEROMONE_DECAY,
    GRID_HEIGHT,
    GRID_WIDTH,
    HOME_PHEROMONE_DECAY,
    NEST_SIZE,
    PHEROMONE_MAX,
)
from sim.world import EMPTY, FOOD, NEST, World


class WorldTests(unittest.TestCase):
    def test_world_has_expected_size(self) -> None:
        """Verify the world starts with the expected grid dimensions."""
        world = World(seed=123)

        self.assertEqual(world.width, GRID_WIDTH)
        self.assertEqual(world.height, GRID_HEIGHT)
        self.assertEqual(world.cell_type.shape, (GRID_HEIGHT, GRID_WIDTH))
        self.assertEqual(world.food_amount.shape, (GRID_HEIGHT, GRID_WIDTH))

    def test_nest_cells_match_center_block(self) -> None:
        """Verify the centered nest is created with the expected number of cells."""
        world = World(seed=123)

        nest_cells = world.nest_cells()

        self.assertEqual(len(nest_cells), NEST_SIZE * NEST_SIZE)
        self.assertEqual(int((world.cell_type == NEST).sum()), NEST_SIZE * NEST_SIZE)
        self.assertIn((32, 32), nest_cells)

    def test_food_is_initialized(self) -> None:
        """Verify food patches are created and total food matches the configured amount."""
        world = World(seed=123)

        expected_total_food = FOOD_PATCH_COUNT * FOOD_PER_PATCH
        food_cell_count = int((world.cell_type == FOOD).sum())

        self.assertEqual(world.total_food(), expected_total_food)
        self.assertEqual(food_cell_count, FOOD_PATCH_COUNT * 9)

    def test_reset_restores_seeded_layout(self) -> None:
        """Verify reset rebuilds the arrays back to their initial seeded state."""
        world = World(seed=123)

        original_cell_type = world.cell_type.copy()
        original_food_amount = world.food_amount.copy()

        world.food_amount[0, 0] = 99
        world.cell_type[0, 0] = FOOD

        world.reset(seed=123)

        self.assertTrue((world.cell_type == original_cell_type).all())
        self.assertTrue((world.food_amount == original_food_amount).all())

    def test_consume_food_reduces_amount_and_clears_empty_cells(self) -> None:
        """Consuming the final food unit should remove the food cell from the world."""
        world = World(seed=123)
        food_y, food_x = next(zip(*((world.cell_type == FOOD).nonzero())))
        starting_food = int(world.food_amount[food_y, food_x])

        for _ in range(starting_food - 1):
            self.assertTrue(world.consume_food(food_x, food_y))

        self.assertEqual(int(world.food_amount[food_y, food_x]), 1)
        self.assertEqual(int(world.cell_type[food_y, food_x]), FOOD)

        self.assertTrue(world.consume_food(food_x, food_y))
        self.assertEqual(int(world.food_amount[food_y, food_x]), 0)
        self.assertEqual(int(world.cell_type[food_y, food_x]), EMPTY)

    def test_evaporate_pheromones_decays_and_clamps_small_values(self) -> None:
        """Pheromone layers should decay each tick and clamp tiny values to zero."""
        world = World(seed=123)

        world.home_pheromone[1, 1] = 2.0
        world.food_pheromone[2, 2] = 3.0
        world.home_pheromone[3, 3] = 0.001
        world.food_pheromone[4, 4] = 0.0005

        world.evaporate_pheromones()

        self.assertEqual(float(world.home_pheromone[1, 1]), 2.0 * HOME_PHEROMONE_DECAY)
        self.assertEqual(float(world.food_pheromone[2, 2]), 3.0 * FOOD_PHEROMONE_DECAY)
        self.assertEqual(float(world.home_pheromone[3, 3]), 0.0)
        self.assertEqual(float(world.food_pheromone[4, 4]), 0.0)

    def test_deposit_pheromones_cap_at_configured_maximum(self) -> None:
        """Deposits should saturate at the configured pheromone ceiling."""
        world = World(seed=123)

        world.home_pheromone[1, 1] = PHEROMONE_MAX - 0.25
        world.food_pheromone[2, 2] = PHEROMONE_MAX - 0.25

        world.deposit_home_pheromone(1, 1, amount=1.0)
        world.deposit_food_pheromone(2, 2)

        self.assertEqual(float(world.home_pheromone[1, 1]), PHEROMONE_MAX)
        self.assertEqual(float(world.food_pheromone[2, 2]), PHEROMONE_MAX)


if __name__ == "__main__":
    unittest.main()
