import random
import unittest

from sim.ant import Ant, DIRECTION_OFFSETS
from sim.config import MAX_ENERGY, MOVE_COST


class AntTests(unittest.TestCase):
    def test_ant_starts_with_expected_default_state(self) -> None:
        """A new ant should use the configured defaults for its state fields."""
        ant = Ant(x=10, y=11, direction=2)

        self.assertEqual(ant.x, 10)
        self.assertEqual(ant.y, 11)
        self.assertEqual(ant.direction, 2)
        self.assertEqual(ant.energy, MAX_ENERGY)
        self.assertFalse(ant.carrying_food)
        self.assertTrue(ant.alive)

    def test_step_moves_to_a_valid_forward_choice_and_spends_energy(self) -> None:
        """Stepping should move to one valid local direction and reduce energy by one."""
        ant = Ant(x=5, y=5, direction=2)
        rng = random.Random(123)
        valid_directions = {1, 2, 3}

        ant.step(width=64, height=64, rng=rng)

        moved_dx = ant.x - 5
        moved_dy = ant.y - 5

        self.assertIn(ant.direction, valid_directions)
        self.assertIn((moved_dx, moved_dy), {DIRECTION_OFFSETS[index] for index in valid_directions})
        self.assertEqual(ant.energy, MAX_ENERGY - MOVE_COST)
        self.assertTrue(ant.alive)

    def test_step_turns_around_when_all_choices_are_out_of_bounds(self) -> None:
        """A blocked ant should stay put, reverse direction, and spend the tick."""
        ant = Ant(x=0, y=0, direction=7)
        rng = random.Random(123)

        ant.step(width=1, height=1, rng=rng)

        self.assertEqual((ant.x, ant.y), (0, 0))
        self.assertEqual(ant.direction, 3)
        self.assertEqual(ant.energy, MAX_ENERGY - MOVE_COST)

    def test_blocked_ant_can_move_away_from_edge_on_next_step(self) -> None:
        """Reversing in place should let a wall-facing ant leave the border next tick."""
        ant = Ant(x=0, y=0, direction=7)
        rng = random.Random(123)

        ant.step(width=2, height=2, rng=rng)
        ant.step(width=2, height=2, rng=rng)

        self.assertNotEqual((ant.x, ant.y), (0, 0))
        self.assertIn((ant.x, ant.y), {(1, 0), (1, 1), (0, 1)})

    def test_step_marks_ant_dead_when_energy_reaches_zero(self) -> None:
        """An ant should become dead as soon as its post-step energy is depleted."""
        ant = Ant(x=3, y=3, direction=0, energy=MOVE_COST)
        rng = random.Random(123)

        ant.step(width=64, height=64, rng=rng)

        self.assertEqual(ant.energy, 0)
        self.assertFalse(ant.alive)

    def test_dead_ant_does_not_move_or_spend_energy(self) -> None:
        """Dead ants should stop interacting with the simulation."""
        ant = Ant(x=7, y=8, direction=4, energy=10, alive=False)
        rng = random.Random(123)

        ant.step(width=64, height=64, rng=rng)

        self.assertEqual((ant.x, ant.y), (7, 8))
        self.assertEqual(ant.direction, 4)
        self.assertEqual(ant.energy, 10)


if __name__ == "__main__":
    unittest.main()
