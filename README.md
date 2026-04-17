# Ants

Minimal ant simulation project scaffold.

Core simulation code lives in the `sim/` package.

## Setup

1. Install Python 3.13.
2. Run `setup.bat`
3. Activate the environment with `.venv\Scripts\activate`
4. Run the project with `run.bat`

`run.bat` expects `main.py` in the project root.

## Controls

- `Space`: pause or resume the simulation
- `R`: reset the simulation
- `Esc`: exit
- Window close button: exit

## Checks

Run both mypy and the unit tests with:

`test.bat`

You can also run them separately if you want:

Run the unit tests with:

`python -m unittest discover -s tests`

Run the static type checker with:

`python -m mypy sim/config.py sim/world.py sim/render.py sim/ant.py sim/sim.py main.py tests/test_world.py tests/test_render.py tests/test_ant.py tests/test_sim.py`
