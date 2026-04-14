from __future__ import annotations

import pygame

from sim.config import FPS, WINDOW_TITLE
from sim.render import Renderer
from sim.world import World


def main() -> None:
    """Run with:
    pip install numpy pygame
    python main.py
    """
    pygame.init()

    world = World()
    renderer = Renderer(world)
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
                    world = World()
                    renderer.set_world(world)

        renderer.draw(screen)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
