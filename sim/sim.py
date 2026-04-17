from __future__ import annotations

import random
from typing import Optional

from sim.ant import Ant
from sim.config import ANT_COUNT
from sim.world import World


class Simulation:
    def __init__(self, seed: Optional[int] = None) -> None:
        """Build the world and ant list for the current simulation step."""
        self.world = World(seed=seed)
        self.random = random.Random(seed)
        self.ants: list[Ant] = []
        self.tick = 0
        self._spawn_ants()

    def step(self) -> None:
        """Advance the simulation by one tick by updating ants in random order."""
        living_ants = [ant for ant in self.ants if ant.alive]
        self.random.shuffle(living_ants)

        for ant in living_ants:
            ant.step(width=self.world.width, height=self.world.height, rng=self.random)

        self.tick += 1

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
