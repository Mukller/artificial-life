<div align="center">

[Русский](README.md) • **English**

</div>

# artificial-life

Digital life in 300 lines of Python.

Cells eat, divide, die. Evolution happens on its own — no clever code, just simple rules and natural selection.

## What's inside

- **Environment** — a grid with food that grows randomly
- **Organisms** — energy, genome (speed/size/perception), age
- **Evolution** — genome mutates on division, weak ones die faster
- **Visualization** — ASCII in terminal or a pygame window

## Run

```bash
pip install pygame
python life.py          # pygame window
python life.py --ascii  # terminal output
```

Flags:
```
--width   grid width (default 80)
--height  grid height (default 40)
--seed    initial organism count
--fps     frames per second
```

## Genome

```python
genome = {
    "speed":      float,  # cells moved per tick
    "perception": float,  # food detection radius
    "size":       float,  # affects energy consumption
    "mutation":   float,  # mutation probability for offspring
}
```

Every trait is a trade-off. Faster means hungrier. Larger means slower.
