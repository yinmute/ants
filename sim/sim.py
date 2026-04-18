from __future__ import annotations

import random
from typing import Optional

from sim.ant import Ant, DIRECTION_OFFSETS
from sim.config import ANT_COUNT, DEPOSIT_HOME, HOME_PHEROMONE_FATIGUE, MAX_ENERGY, PHEROMONE_FOLLOW_THRESHOLD
from sim.world import FOOD, NEST, GridFloat, World


class Simulation:
    def __init__(self, seed: Optional[int] = None) -> None:
        """Build the world and ant list for the current simulation step."""
        self.world = World(seed=seed)
        self.random = random.Random(seed)
        self.nest_center_x = self.world.width // 2
        self.nest_center_y = self.world.height // 2
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
        self.world.evaporate_pheromones()

        living_ants = [ant for ant in self.ants if ant.alive]
        self.random.shuffle(living_ants)

        for ant in living_ants:
            preferred_direction = self._choose_direction_for_ant(ant)
            ant.step(
                width=self.world.width,
                height=self.world.height,
                rng=self.random,
                preferred_direction=preferred_direction,
            )
            self._deposit_pheromone(ant)
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
            ant.wander_steps = 0
            ant.energy = MAX_ENERGY
            ant.reverse_direction()

    def _deposit_pheromone(self, ant: Ant) -> None:
        """Leave a pheromone mark on the cell the ant occupies after moving."""
        if not ant.alive:
            return

        if ant.carrying_food:
            ant.wander_steps = 0
            self.world.deposit_food_pheromone(ant.x, ant.y)
        else:
            ant.wander_steps += 1
            self.world.deposit_home_pheromone(
                ant.x,
                ant.y,
                amount=DEPOSIT_HOME * (HOME_PHEROMONE_FATIGUE ** ant.wander_steps),
            )

    def _handle_nest_interaction(self, ant: Ant) -> None:
        """Let a carrying ant drop food when it reaches the nest."""
        if not ant.alive or not ant.carrying_food:
            return

        if self.world.cell_type[ant.y, ant.x] == NEST:
            ant.carrying_food = False
            ant.wander_steps = 0
            self.delivered_food += 1
            ant.reverse_direction()

    def _choose_direction_for_ant(self, ant: Ant) -> int | None:
        """Choose a local target direction based on food, nest, and pheromones."""
        candidate_moves = self._candidate_moves(ant)

        if ant.carrying_food:
            nest_directions = self._nest_directions_for(candidate_moves)
            if nest_directions:
                return self.random.choice(nest_directions)

            return self._best_pheromone_direction(
                ant,
                candidate_moves,
                self.world.home_pheromone,
                prefer_nest_distance=True,
            )

        food_directions = self._food_directions_for(ant, candidate_moves)
        if food_directions:
            return self.random.choice(food_directions)

        return self._best_pheromone_direction(ant, candidate_moves, self.world.food_pheromone)

    def _candidate_moves(self, ant: Ant) -> list[tuple[int, int, int]]:
        """Return valid forward candidate moves as direction and destination."""
        candidate_moves: list[tuple[int, int, int]] = []

        for direction in ant.candidate_directions():
            new_x, new_y = ant.position_in_direction(direction)

            if 0 <= new_x < self.world.width and 0 <= new_y < self.world.height:
                candidate_moves.append((direction, new_x, new_y))

        return candidate_moves

    def _food_directions_for(self, ant: Ant, candidate_moves: list[tuple[int, int, int]]) -> list[int]:
        """Collect the candidate directions that lead toward the nearest seen food."""
        best_distance: int | None = None
        best_food_amount = 0
        best_directions: list[int] = []

        for direction, _, _ in candidate_moves:
            for distance in range(1, 4):
                new_x, new_y = ant.position_in_direction(direction, distance=distance)

                if not (0 <= new_x < self.world.width and 0 <= new_y < self.world.height):
                    break

                if self.world.cell_type[new_y, new_x] != FOOD:
                    continue

                food_amount = int(self.world.food_amount[new_y, new_x])
                if food_amount <= 0:
                    continue

                if best_distance is None or distance < best_distance:
                    best_distance = distance
                    best_food_amount = food_amount
                    best_directions = [direction]
                elif distance == best_distance:
                    if food_amount > best_food_amount:
                        best_food_amount = food_amount
                        best_directions = [direction]
                    elif food_amount == best_food_amount:
                        best_directions.append(direction)

                # The closest food along one ray is enough to choose that direction.
                break

        return best_directions

    def _nest_directions_for(self, candidate_moves: list[tuple[int, int, int]]) -> list[int]:
        """Collect the candidate directions that lead directly onto nest cells."""
        nest_directions: list[int] = []

        for direction, new_x, new_y in candidate_moves:
            if self.world.cell_type[new_y, new_x] == NEST:
                nest_directions.append(direction)

        return nest_directions

    def _best_pheromone_direction(
        self,
        ant: Ant,
        candidate_moves: list[tuple[int, int, int]],
        pheromone_grid: GridFloat,
        prefer_nest_distance: bool = False,
    ) -> int | None:
        """Choose the strongest visible pheromone direction above the follow threshold."""
        best_value = PHEROMONE_FOLLOW_THRESHOLD
        best_distance: int | None = None
        best_nest_distance: int | None = None
        best_directions: list[int] = []

        for direction, _, _ in candidate_moves:
            for distance in range(1, 4):
                new_x, new_y = ant.position_in_direction(direction, distance=distance)

                if not (0 <= new_x < self.world.width and 0 <= new_y < self.world.height):
                    break

                pheromone_value = float(pheromone_grid[new_y, new_x])
                if pheromone_value <= PHEROMONE_FOLLOW_THRESHOLD:
                    continue

                nest_distance = self._nest_distance_sq(new_x, new_y)

                if prefer_nest_distance and best_nest_distance is not None and nest_distance > best_nest_distance:
                    continue

                if prefer_nest_distance and (best_nest_distance is None or nest_distance < best_nest_distance):
                    best_nest_distance = nest_distance
                    best_value = pheromone_value
                    best_distance = distance
                    best_directions = [direction]
                elif pheromone_value > best_value:
                    best_value = pheromone_value
                    best_distance = distance
                    best_nest_distance = nest_distance
                    best_directions = [direction]
                elif pheromone_value == best_value:
                    if prefer_nest_distance and best_nest_distance is not None and nest_distance < best_nest_distance:
                        best_nest_distance = nest_distance
                        best_distance = distance
                        best_directions = [direction]
                    elif best_distance is None or distance < best_distance:
                        best_distance = distance
                        best_nest_distance = nest_distance
                        best_directions = [direction]
                    elif distance == best_distance:
                        best_directions.append(direction)

        if not best_directions:
            return None

        return self.random.choice(best_directions)

    def _nest_distance_sq(self, x: int, y: int) -> int:
        """Return squared distance from a cell to the nest center."""
        dx = x - self.nest_center_x
        dy = y - self.nest_center_y
        return dx * dx + dy * dy

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
