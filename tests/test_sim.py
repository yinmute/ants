import unittest

from sim.config import (
    ANT_COUNT,
    DEPOSIT_FOOD,
    DEPOSIT_HOME,
    HOME_PHEROMONE_FATIGUE,
    MAX_ENERGY,
    MOVE_COST,
    PHEROMONE_FOLLOW_THRESHOLD,
)
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
            self.assertEqual(ant.wander_steps, 0)
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

    def test_choose_direction_for_carrying_ant_uses_seen_nest_cell(self) -> None:
        """A carrying ant should choose a nest cell in its forward candidate cells."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 10
        ant.y = 10
        ant.direction = 2
        ant.carrying_food = True

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.cell_type[10, 11] = NEST

        chosen_direction = simulation._choose_direction_for_ant(ant)

        self.assertEqual(chosen_direction, 2)

    def test_choose_direction_for_non_carrying_ant_uses_seen_food_cell(self) -> None:
        """A non-carrying ant should choose the richest seen food cell first."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 10
        ant.y = 10
        ant.direction = 2
        ant.carrying_food = False

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.food_amount[:, :] = 0
        simulation.world.cell_type[9, 11] = FOOD
        simulation.world.food_amount[9, 11] = 2
        simulation.world.cell_type[10, 11] = FOOD
        simulation.world.food_amount[10, 11] = 5

        chosen_direction = simulation._choose_direction_for_ant(ant)

        self.assertEqual(chosen_direction, 2)

    def test_choose_direction_for_non_carrying_ant_sees_food_at_distance_two(self) -> None:
        """A non-carrying ant should steer toward food seen two cells ahead."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 10
        ant.y = 10
        ant.direction = 2
        ant.carrying_food = False

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.food_amount[:, :] = 0
        simulation.world.cell_type[10, 12] = FOOD
        simulation.world.food_amount[10, 12] = 4

        chosen_direction = simulation._choose_direction_for_ant(ant)

        self.assertEqual(chosen_direction, 2)

    def test_choose_direction_for_non_carrying_ant_sees_food_at_distance_three(self) -> None:
        """A non-carrying ant should steer toward food seen three cells ahead."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 10
        ant.y = 10
        ant.direction = 2
        ant.carrying_food = False

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.food_amount[:, :] = 0
        simulation.world.cell_type[10, 13] = FOOD
        simulation.world.food_amount[10, 13] = 4

        chosen_direction = simulation._choose_direction_for_ant(ant)

        self.assertEqual(chosen_direction, 2)

    def test_choose_direction_for_non_carrying_ant_follows_food_pheromone(self) -> None:
        """A non-carrying ant should follow the strongest local food pheromone."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 10
        ant.y = 10
        ant.direction = 2
        ant.carrying_food = False

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.food_amount[:, :] = 0
        simulation.world.food_pheromone[:, :] = 0.0
        simulation.world.food_pheromone[9, 11] = PHEROMONE_FOLLOW_THRESHOLD + 0.01
        simulation.world.food_pheromone[10, 11] = PHEROMONE_FOLLOW_THRESHOLD + 0.02

        chosen_direction = simulation._choose_direction_for_ant(ant)

        self.assertEqual(chosen_direction, 2)

    def test_choose_direction_for_carrying_ant_follows_home_pheromone(self) -> None:
        """A carrying ant should follow the strongest local home pheromone."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 10
        ant.y = 10
        ant.direction = 2
        ant.carrying_food = True

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.home_pheromone[:, :] = 0.0
        simulation.world.home_pheromone[11, 11] = PHEROMONE_FOLLOW_THRESHOLD + 0.03
        simulation.world.home_pheromone[10, 11] = PHEROMONE_FOLLOW_THRESHOLD + 0.01

        chosen_direction = simulation._choose_direction_for_ant(ant)

        self.assertEqual(chosen_direction, 3)

    def test_choose_direction_for_carrying_ant_follows_home_pheromone_at_distance_three(self) -> None:
        """A carrying ant should see home pheromone farther ahead along its forward cone."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 10
        ant.y = 10
        ant.direction = 2
        ant.carrying_food = True

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.home_pheromone[:, :] = 0.0
        simulation.world.home_pheromone[10, 13] = PHEROMONE_FOLLOW_THRESHOLD + 0.02

        chosen_direction = simulation._choose_direction_for_ant(ant)

        self.assertEqual(chosen_direction, 2)

    def test_choose_direction_for_carrying_ant_prefers_trail_closer_to_nest(self) -> None:
        """A carrying ant should prefer the home trail that heads more directly nest-ward."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 40
        ant.y = 40
        ant.direction = 6
        ant.carrying_food = True

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.home_pheromone[:, :] = 0.0
        simulation.world.home_pheromone[39, 39] = PHEROMONE_FOLLOW_THRESHOLD + 0.10
        simulation.world.home_pheromone[41, 39] = PHEROMONE_FOLLOW_THRESHOLD + 0.30

        chosen_direction = simulation._choose_direction_for_ant(ant)

        self.assertEqual(chosen_direction, 7)

    def test_choose_direction_ignores_pheromone_values_at_threshold(self) -> None:
        """Pheromone values must beat the threshold before they influence movement."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 10
        ant.y = 10
        ant.direction = 2
        ant.carrying_food = False

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.food_amount[:, :] = 0
        simulation.world.food_pheromone[:, :] = 0.0
        simulation.world.food_pheromone[10, 11] = PHEROMONE_FOLLOW_THRESHOLD

        chosen_direction = simulation._choose_direction_for_ant(ant)

        self.assertIsNone(chosen_direction)

    def test_step_deposits_home_pheromone_for_non_carrying_ant(self) -> None:
        """A non-carrying ant should leave home pheromone on the cell it reaches."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 0
        ant.y = 1
        ant.direction = 7
        ant.carrying_food = False
        ant.alive = True

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.home_pheromone[:, :] = 0.0
        simulation.world.food_pheromone[:, :] = 0.0

        for other_ant in simulation.ants[1:]:
            other_ant.alive = False

        simulation.step()

        self.assertEqual((ant.x, ant.y), (0, 0))
        self.assertAlmostEqual(
            float(simulation.world.home_pheromone[0, 0]),
            DEPOSIT_HOME * HOME_PHEROMONE_FATIGUE,
        )
        self.assertEqual(float(simulation.world.food_pheromone[0, 0]), 0.0)
        self.assertEqual(ant.wander_steps, 1)

    def test_home_pheromone_deposit_gets_weaker_with_more_wandering(self) -> None:
        """Longer wandering should reduce the amount of home pheromone deposited."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 5
        ant.y = 5
        ant.direction = 2
        ant.carrying_food = False
        ant.alive = True
        ant.wander_steps = 9

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.home_pheromone[:, :] = 0.0
        simulation.world.food_pheromone[:, :] = 0.0

        simulation._deposit_pheromone(ant)

        self.assertEqual(ant.wander_steps, 10)
        self.assertAlmostEqual(
            float(simulation.world.home_pheromone[5, 5]),
            DEPOSIT_HOME * (HOME_PHEROMONE_FATIGUE ** 10),
        )

    def test_picking_up_food_resets_wandering_fatigue(self) -> None:
        """Picking up food should reset the wandering count used for home deposits."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 5
        ant.y = 5
        ant.direction = 2
        ant.energy = 12
        ant.carrying_food = False
        ant.wander_steps = 14
        ant.alive = True

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.food_amount[:, :] = 0
        simulation.world.cell_type[5, 5] = FOOD
        simulation.world.food_amount[5, 5] = 1

        simulation._handle_food_interaction(ant)

        self.assertTrue(ant.carrying_food)
        self.assertEqual(ant.wander_steps, 0)

    def test_step_deposits_food_pheromone_for_carrying_ant(self) -> None:
        """A carrying ant should leave food pheromone on the cell it reaches."""
        simulation = Simulation(seed=123)
        ant = simulation.ants[0]

        ant.x = 0
        ant.y = 1
        ant.direction = 7
        ant.carrying_food = True
        ant.alive = True

        simulation.world.cell_type[:, :] = EMPTY
        simulation.world.home_pheromone[:, :] = 0.0
        simulation.world.food_pheromone[:, :] = 0.0

        for other_ant in simulation.ants[1:]:
            other_ant.alive = False

        simulation.step()

        self.assertEqual((ant.x, ant.y), (0, 0))
        self.assertEqual(float(simulation.world.home_pheromone[0, 0]), 0.0)
        self.assertEqual(float(simulation.world.food_pheromone[0, 0]), DEPOSIT_FOOD)
        self.assertEqual(ant.wander_steps, 0)

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
