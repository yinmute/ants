from __future__ import annotations

import pygame

from sim.config import FPS, WINDOW_TITLE
from sim.render import Renderer
from sim.sim import Simulation


def print_metrics(simulation: Simulation) -> None:
    """Print a small sanity snapshot so movement can be checked without ant rendering."""
    living_ants = [ant for ant in simulation.ants if ant.alive]
    average_energy = 0.0
    if living_ants:
        average_energy = sum(ant.energy for ant in living_ants) / len(living_ants)

    sample_positions = [(ant.x, ant.y) for ant in simulation.ants[:5]]
    print(
        f"tick={simulation.tick} "
        f"living_ants={len(living_ants)} "
        f"average_energy={average_energy:.2f} "
        f"sample_positions={sample_positions}"
    )


def main() -> None:
    """Run with:
    pip install numpy pygame
    python main.py
    """
    pygame.init()

    simulation = Simulation()
    renderer = Renderer(simulation.world)
    screen = pygame.display.set_mode((renderer.width, renderer.height))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    simulation = Simulation()
                    renderer.set_world(simulation.world)

        simulation.step()
        if simulation.tick % 30 == 0:
            print_metrics(simulation)

        renderer.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
