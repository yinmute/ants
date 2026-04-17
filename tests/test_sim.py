import unittest

from sim.config import ANT_COUNT, MAX_ENERGY, MOVE_COST
from sim.sim import Simulation


class SimulationTests(unittest.TestCase):
    def test_simulation_spawns_configured_number_of_ants_inside_nest(self) -> None:
        """All ants should start in nest cells with full energy and valid directions."""
        simulation = Simulation(seed=123)
        nest_cells = set(simulation.world.nest_cells())

        self.assertEqual(len(simulation.ants), ANT_COUNT)
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

    def test_repeated_steps_eventually_kill_all_ants(self) -> None:
        """With no energy refill yet, all ants should eventually die."""
        simulation = Simulation(seed=123)

        for _ in range(MAX_ENERGY):
            simulation.step()

        self.assertTrue(all(not ant.alive for ant in simulation.ants))
        self.assertEqual(simulation.tick, MAX_ENERGY)


if __name__ == "__main__":
    unittest.main()
