"""Shared configuration values for the current simulation step."""

# World grid settings used by World to allocate the main arrays.
GRID_WIDTH = 64
GRID_HEIGHT = 64

# World layout settings used by World when placing the nest and food.
NEST_SIZE = 3
FOOD_PATCH_COUNT = 3
FOOD_PER_PATCH = 80

# Ant settings used by Ant and Simulation when spawning and updating ants.
ANT_COUNT = 30
MAX_ENERGY = 200
MOVE_COST = 1

# App loop settings used by main.py when creating the window and ticking pygame.
WINDOW_TITLE = "Swarm Ants v1"
FPS = 30

# Render sizing used by Renderer to convert grid cells into screen pixels.
CELL_SIZE = 10

# Render colors used by Renderer when drawing world cell types.
COLOR_EMPTY = (20, 20, 20)
COLOR_NEST = (50, 100, 220)
COLOR_FOOD = (60, 180, 75)
