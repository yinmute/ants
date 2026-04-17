from __future__ import annotations

import pygame

from sim.config import FPS, WINDOW_TITLE
from sim.render import OverlayState, Renderer
from sim.sim import Simulation


def draw_frame(
    screen: pygame.Surface,
    renderer: Renderer,
    simulation: Simulation,
    paused: bool,
) -> None:
    """Draw the current world, ants, and small status overlay."""
    living_ants = sum(1 for ant in simulation.ants if ant.alive)

    renderer.draw(screen)
    renderer.draw_ants(screen, simulation.ants)
    renderer.draw_overlay(
        screen,
        OverlayState(
            tick=simulation.tick,
            living_ants=living_ants,
            paused=paused,
        ),
    )
    pygame.display.flip()


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
    paused = False

    running = True
    while running:
        reset_requested = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_r:
                    reset_requested = True

        if not running:
            break

        if reset_requested:
            simulation = Simulation()
            renderer.set_world(simulation.world)
            draw_frame(screen, renderer, simulation, paused)
            clock.tick(FPS)
            continue

        if not paused:
            simulation.step()

        draw_frame(screen, renderer, simulation, paused)
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
