import unittest

from sim.config import FOOD_PATCH_COUNT, FOOD_PER_PATCH, GRID_HEIGHT, GRID_WIDTH, NEST_SIZE
from sim.world import FOOD, NEST, World


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


if __name__ == "__main__":
    unittest.main()
