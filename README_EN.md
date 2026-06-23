# artificial-life

Digital life in 300 lines of Python.

Cells eat, divide, die. Evolution happens on its own — no clever algorithms, just simple rules and natural selection.

## What's inside

- **Environment** — a grid with food. Food grows randomly.
- **Organisms** — each has energy, a genome (speed/size/perception), and age.
- **Evolution** — genome mutates on division. Weak ones die faster.
- **Visualization** — ASCII to terminal or pygame window.

## Usage

```bash
pip install pygame
python life.py          # pygame window
python life.py --ascii  # in the terminal
```

Options:
```
--width   grid width (default 80)
--height  grid height (default 40)
--seed    initial organism count
--fps     frames per second
```

## What to watch

Run it and wait 5 minutes. Watch how:
- population first explodes, then collapses
- those with optimal speed/perception balance survive
- dominant clones sometimes emerge

## Genome structure

```python
genome = {
    "speed":      float,  # cells moved per turn
    "perception": float,  # food "vision" radius
    "size":       float,  # affects energy consumption
    "mutation":   float,  # offspring mutation probability
}
```

Every parameter is a trade-off. Fast burns more energy. Large sees further but moves slower.
