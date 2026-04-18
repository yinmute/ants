from __future__ import annotations

import random
from typing import Optional

from sim.ant import Ant, DIRECTION_OFFSETS
from sim.config import ANT_COUNT, MAX_ENERGY
from sim.world import NEST, World


class Simulation:
    def __init__(self, seed: Optional[int] = None) -> None:
        """Build the world and ant list for the current simulation step."""
        self.world = World(seed=seed)
        self.random = random.Random(seed)
        self.ants: list[Ant] = []
        self.tick = 0
        self.living_ants = 0
        self.ants_carrying_food = 0
        self.delivered_food = 0
        self.remaining_total_food = 0
        self._spawn_ants()
        self._update_counts()

    def step(self) -> None:
        """Advance the simulation by one tick by updating ants in random order."""
        living_ants = [ant for ant in self.ants if ant.alive]
        self.random.shuffle(living_ants)

        for ant in living_ants:
            forced_direction = self._find_nest_direction(ant) if ant.carrying_food else None
            ant.step(
                width=self.world.width,
                height=self.world.height,
                rng=self.random,
                forced_direction=forced_direction,
            )
            if ant.carrying_food:
                self._handle_nest_interaction(ant)
            else:
                self._handle_food_interaction(ant)

        self.tick += 1
        self._update_counts()

        if self.tick % 30 == 0:
            self._print_metrics()

    def _spawn_ants(self) -> None:
        """Place all ants randomly inside the nest with random initial directions."""
        nest_cells = self.world.nest_cells()
        self.ants = [
            Ant(
                x=x,
                y=y,
                direction=self.random.randrange(8),
            )
            for x, y in (self.random.choice(nest_cells) for _ in range(ANT_COUNT))
        ]

    def _handle_food_interaction(self, ant: Ant) -> None:
        """Let a non-carrying ant pick up food from the cell it ends on."""
        if not ant.alive or ant.carrying_food:
            return

        if self.world.consume_food(ant.x, ant.y):
            ant.carrying_food = True
            ant.energy = MAX_ENERGY
            ant.reverse_direction()

    def _handle_nest_interaction(self, ant: Ant) -> None:
        """Let a carrying ant drop food when it reaches the nest."""
        if not ant.alive or not ant.carrying_food:
            return

        if self.world.cell_type[ant.y, ant.x] == NEST:
            ant.carrying_food = False
            self.delivered_food += 1
            ant.reverse_direction()

    def _find_nest_direction(self, ant: Ant) -> int | None:
        """Choose a one-step move into a nearby nest cell when one is visible."""
        forward_nest_directions = self._nest_directions_for(ant, ant.candidate_directions())
        if forward_nest_directions:
            return self.random.choice(forward_nest_directions)

        adjacent_directions = list(range(len(DIRECTION_OFFSETS)))
        adjacent_nest_directions = self._nest_directions_for(ant, adjacent_directions)
        if adjacent_nest_directions:
            return self.random.choice(adjacent_nest_directions)

        return None

    def _nest_directions_for(self, ant: Ant, directions: list[int]) -> list[int]:
        """Collect the valid one-step directions that lead directly onto nest cells."""
        nest_directions: list[int] = []

        for direction in directions:
            dx, dy = DIRECTION_OFFSETS[direction]
            new_x = ant.x + dx
            new_y = ant.y + dy

            if 0 <= new_x < self.world.width and 0 <= new_y < self.world.height:
                if self.world.cell_type[new_y, new_x] == NEST:
                    nest_directions.append(direction)

        return nest_directions

    def _update_counts(self) -> None:
        """Refresh the small counters derived from the current ant states."""
        self.living_ants = sum(1 for ant in self.ants if ant.alive)
        self.ants_carrying_food = sum(1 for ant in self.ants if ant.alive and ant.carrying_food)
        self.remaining_total_food = self.world.total_food()

    def _print_metrics(self) -> None:
        """Print a compact snapshot of the current simulation state."""
        print(
            f"tick={self.tick} "
            f"living_ants={self.living_ants} "
            f"delivered_food={self.delivered_food} "
            f"ants_carrying_food={self.ants_carrying_food} "
            f"remaining_total_food={self.remaining_total_food}"
        )
