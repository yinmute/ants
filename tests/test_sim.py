import unittest

from sim.config import ANT_COUNT, MAX_ENERGY, MOVE_COST
from sim.sim import Simulation
from sim.world import EMPTY, FOOD, NEST


class SimulationTests(unittest.TestCase):
    def test_simulation_spawns_configured_number_of_ants_inside_nest(self) -> None:
        """All ants should start in nest cells with full energy and valid directions."""
        simulation = Simulation(seed=123)
        nest_cells = set(simulation.world.nest_cells())

        self.assertEqual(len(simulation.ants), ANT_COUNT)
        self.assertEqual(simulation.living_ants, ANT_COUNT)
        self.assertEqual(simulation.delivered_food, 0)
        self.assertEqual(simulation.ants_carrying_food, 0)
        self.assertEqual(simulation.remaining_total_food, simulation.world.total_food())
        for ant in simulation.ants:
            self.assertIn((ant.x, ant.y), nest_cells)
            self.assertEqual(ant.energy, MAX_ENERGY)
            self.assertIn(ant.direction, range(8))
            self.assertTrue(ant.alive)

    def test_step_increments_tick_and_updates_living_ants(self) -> None:
        """A simulation step should advance time and spend one energy on living ants."""
        simulation = Simulation(seed=123)
        starting_positions = [(ant.x, ant.y) for ant in simulation.ants]

        simulation.step()

        self.assertEqual(simulation.tick, 1)
        self.assertTrue(all(ant.energy == MAX_ENERGY - MOVE_COST for ant in simulation.ants))
        self.assertTrue(any((ant.x, ant.y) != start for ant, start in zip(simulation.ants, starting_positions)))

    def test_step_skips_dead_ants(self) -> None:
        """Dead ants should remain unchanged when the simulation advances."""
        simulation = Simulation(seed=123)
        dead_ant = simulation.ants[0]
        living_ant = simulation.ants[1]

        dead_ant.alive = False
        dead_ant.energy = 5
        dead_position = (dead_ant.x, dead_ant.y, dead_ant.direction)
        living_energy = living_ant.energy

        simulation.step()

        self.assertEqual(dead_ant.energy, 5)
        self.assertEqual((dead_ant.x, dead_ant.y, dead_ant.direction), dead_position)
        self.assertEqual(living_ant.energy, living_energy - MOVE_COST)
        self.assertEqual(simulation.living_ants, ANT_COUNT - 1)

    def test_ant_picks_up_food_refills_energy_and_turns_around(self) -> None:
        """A non-carrying ant should consume food and switch into carrying mode."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 0
        ant.y = 1
        ant.direction = 7
        ant.energy = 5
        ant.carrying_food = False
        ant.alive = True

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.food_amount[:, :] = 0
        simulation.world.cell_type[0, 0] = FOOD
        simulation.world.food_amount[0, 0] = 1

        ant.step(width=simulation.world.width, height=simulation.world.height, rng=simulation.random)
        simulation._handle_food_interaction(ant)

        self.assertEqual((ant.x, ant.y), (0, 0))
        self.assertTrue(ant.carrying_food)
        self.assertEqual(ant.energy, MAX_ENERGY)
        self.assertEqual(ant.direction, 4)
        self.assertEqual(simulation.world.food_amount[0, 0], 0)
        self.assertEqual(simulation.world.cell_type[0, 0], EMPTY)

    def test_step_updates_carrying_food_counter(self) -> None:
        """The simulation should track how many living ants are carrying food."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 0
        ant.y = 1
        ant.direction = 7
        ant.energy = 5
        ant.carrying_food = False
        ant.alive = True

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.food_amount[:, :] = 0
        simulation.world.cell_type[0, 0] = FOOD
        simulation.world.food_amount[0, 0] = 1

        for other_ant in simulation.ants[1:]:
            other_ant.alive = False

        simulation.step()

        self.assertEqual(simulation.tick, 1)
        self.assertEqual(simulation.living_ants, 1)
        self.assertEqual(simulation.ants_carrying_food, 1)

    def test_carrying_ant_moves_into_adjacent_nest_and_delivers_food(self) -> None:
        """A carrying ant should step onto a nearby nest cell and drop food there."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 0
        ant.y = 1
        ant.direction = 7
        ant.energy = 12
        ant.carrying_food = True
        ant.alive = True

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.food_amount[:, :] = 0
        simulation.world.cell_type[0, 0] = NEST

        for other_ant in simulation.ants[1:]:
            other_ant.alive = False

        simulation.step()

        self.assertEqual((ant.x, ant.y), (0, 0))
        self.assertFalse(ant.carrying_food)
        self.assertEqual(ant.direction, 4)
        self.assertEqual(simulation.delivered_food, 1)
        self.assertEqual(simulation.living_ants, 1)
        self.assertEqual(simulation.ants_carrying_food, 0)

    def test_find_nest_direction_uses_forward_nest_cell_when_available(self) -> None:
        """Forward nest cells should be preferred for carrying ants when visible."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 10
        ant.y = 10
        ant.direction = 2

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.cell_type[10, 11] = NEST
        simulation.world.cell_type[9, 10] = NEST

        chosen_direction = simulation._find_nest_direction(ant)

        self.assertEqual(chosen_direction, 2)

    def test_carrying_ant_does_not_pick_up_more_food(self) -> None:
        """An ant already carrying food should leave the food cell unchanged."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 5
        ant.y = 5
        ant.direction = 2
        ant.energy = 17
        ant.carrying_food = True
        ant.alive = True

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.food_amount[:, :] = 0
        simulation.world.cell_type[5, 5] = FOOD
        simulation.world.food_amount[5, 5] = 3

        simulation._handle_food_interaction(ant)

        self.assertTrue(ant.carrying_food)
        self.assertEqual(ant.energy, 17)
        self.assertEqual(ant.direction, 2)
        self.assertEqual(simulation.world.food_amount[5, 5], 3)
        self.assertEqual(simulation.world.cell_type[5, 5], FOOD)

    def test_dead_ant_does_not_pick_up_food(self) -> None:
        """A dead ant should not consume food or change state on a food cell."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 5
        ant.y = 5
        ant.direction = 2
        ant.energy = 0
        ant.carrying_food = False
        ant.alive = False

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.food_amount[:, :] = 0
        simulation.world.cell_type[5, 5] = FOOD
        simulation.world.food_amount[5, 5] = 2

        simulation._handle_food_interaction(ant)

        self.assertFalse(ant.carrying_food)
        self.assertFalse(ant.alive)
        self.assertEqual(simulation.world.food_amount[5, 5], 2)
        self.assertEqual(simulation.world.cell_type[5, 5], FOOD)

    def test_ant_with_last_energy_dies_before_food_pickup(self) -> None:
        """A last-energy ant should die during movement before the pickup hook runs."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 0
        ant.y = 1
        ant.direction = 7
        ant.energy = MOVE_COST
        ant.carrying_food = False
        ant.alive = True

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.food_amount[:, :] = 0
        simulation.world.cell_type[0, 0] = FOOD
        simulation.world.food_amount[0, 0] = 1

        ant.step(width=simulation.world.width, height=simulation.world.height, rng=simulation.random)
        simulation._handle_food_interaction(ant)

        self.assertEqual((ant.x, ant.y), (0, 0))
        self.assertFalse(ant.alive)
        self.assertFalse(ant.carrying_food)
        self.assertEqual(ant.energy, 0)
        self.assertEqual(simulation.world.food_amount[0, 0], 1)
        self.assertEqual(simulation.world.cell_type[0, 0], FOOD)


if __name__ == "__main__":
    unittest.main()
