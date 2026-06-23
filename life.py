"""
artificial-life — цифровая эволюция в 300 строках.

Запуск:  python life.py
         python life.py --ascii
         python life.py --width 120 --height 60 --seed 50
"""

from __future__ import annotations

import argparse
import random
import sys
import time
from dataclasses import dataclass, field
from typing import Optional

# ──────────────────────────────────────────────
# Геном
# ──────────────────────────────────────────────

@dataclass
class Genome:
    speed: float      = 1.0   # клеток за ход
    perception: float = 3.0   # радиус "зрения"
    size: float       = 1.0   # влияет на расход энергии
    mutation: float   = 0.05  # вероятность мутации каждого гена

    def mutate(self) -> "Genome":
        """Вернуть слегка изменённый геном."""
        def m(v: float, lo: float, hi: float) -> float:
            if random.random() < self.mutation:
                v += random.gauss(0, 0.1)
            return max(lo, min(hi, v))

        return Genome(
            speed      = m(self.speed,      0.5, 5.0),
            perception = m(self.perception, 1.0, 8.0),
            size       = m(self.size,       0.5, 3.0),
            mutation   = m(self.mutation,   0.01, 0.3),
        )

    @staticmethod
    def random() -> "Genome":
        return Genome(
            speed      = random.uniform(0.5, 3.0),
            perception = random.uniform(1.0, 6.0),
            size       = random.uniform(0.5, 2.0),
            mutation   = random.uniform(0.01, 0.15),
        )


# ──────────────────────────────────────────────
# Организм
# ──────────────────────────────────────────────

ENERGY_START    = 100.0
ENERGY_PER_FOOD = 30.0
ENERGY_DIVIDE   = 80.0   # сколько нужно чтобы поделиться
ENERGY_MOVE     = 1.0    # базовый расход за движение
ENERGY_IDLE     = 0.3    # расход в покое

@dataclass
class Organism:
    x: int
    y: int
    genome: Genome
    energy: float = ENERGY_START
    age: int = 0

    def tick_cost(self) -> float:
        return ENERGY_IDLE * self.genome.size

    def move_cost(self) -> float:
        return ENERGY_MOVE * self.genome.size * self.genome.speed

    def is_alive(self) -> bool:
        return self.energy > 0

    def divide(self) -> "Organism":
        self.energy /= 2
        return Organism(x=self.x, y=self.y, genome=self.genome.mutate(),
                        energy=self.energy)


# ──────────────────────────────────────────────
# Среда
# ──────────────────────────────────────────────

FOOD_GROW_RATE  = 0.02   # вероятность появления еды в пустой клетке за ход
FOOD_MAX_ENERGY = 30.0

class World:
    def __init__(self, width: int, height: int):
        self.width  = width
        self.height = height
        self.food: list[list[float]] = [
            [0.0] * width for _ in range(height)
        ]
        self.organisms: list[Organism] = []
        self.tick_n = 0

    # ── еда ──────────────────────────────────

    def grow_food(self) -> None:
        for y in range(self.height):
            for x in range(self.width):
                if self.food[y][x] == 0 and random.random() < FOOD_GROW_RATE:
                    self.food[y][x] = random.uniform(5.0, FOOD_MAX_ENERGY)

    def eat_food(self, x: int, y: int) -> float:
        amount = self.food[y][x]
        self.food[y][x] = 0.0
        return amount

    # ── поиск еды ────────────────────────────

    def find_food(self, x: int, y: int, radius: int) -> Optional[tuple[int, int]]:
        best: Optional[tuple[int, int]] = None
        best_val = 0.0
        r = int(radius)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                nx, ny = (x + dx) % self.width, (y + dy) % self.height
                if self.food[ny][nx] > best_val:
                    best_val = self.food[ny][nx]
                    best = (nx, ny)
        return best

    # ── движение ─────────────────────────────

    def step_toward(self, ox: int, oy: int, tx: int, ty: int) -> tuple[int, int]:
        dx = tx - ox
        dy = ty - oy
        # кратчайший путь с учётом тора
        if abs(dx) > self.width  // 2: dx = -dx // abs(dx) if dx != 0 else 0
        if abs(dy) > self.height // 2: dy = -dy // abs(dy) if dy != 0 else 0
        nx = (ox + (1 if dx > 0 else -1 if dx < 0 else 0)) % self.width
        ny = (oy + (1 if dy > 0 else -1 if dy < 0 else 0)) % self.height
        return nx, ny

    # ── тик ──────────────────────────────────

    def tick(self) -> None:
        self.tick_n += 1
        self.grow_food()

        new_orgs: list[Organism] = []

        for org in self.organisms:
            if not org.is_alive():
                continue

            org.age += 1
            org.energy -= org.tick_cost()

            target = self.find_food(org.x, org.y, org.genome.perception)
            if target:
                steps = max(1, int(org.genome.speed))
                for _ in range(steps):
                    if (org.x, org.y) == target:
                        org.energy += self.eat_food(org.x, org.y) * (1 / org.genome.size)
                        break
                    org.x, org.y = self.step_toward(org.x, org.y, *target)
                    org.energy -= org.move_cost()
            else:
                # бродим случайно
                org.x = (org.x + random.randint(-1, 1)) % self.width
                org.y = (org.y + random.randint(-1, 1)) % self.height
                org.energy -= org.move_cost()

            # деление
            if org.energy >= ENERGY_DIVIDE:
                child = org.divide()
                new_orgs.append(child)

        self.organisms = [o for o in self.organisms if o.is_alive()] + new_orgs

    # ── статистика ───────────────────────────

    def stats(self) -> dict:
        if not self.organisms:
            return {"count": 0, "avg_energy": 0,
                    "avg_speed": 0, "avg_perception": 0, "avg_size": 0}
        n = len(self.organisms)
        return {
            "count":          n,
            "avg_energy":     sum(o.energy            for o in self.organisms) / n,
            "avg_speed":      sum(o.genome.speed      for o in self.organisms) / n,
            "avg_perception": sum(o.genome.perception for o in self.organisms) / n,
            "avg_size":       sum(o.genome.size       for o in self.organisms) / n,
        }


# ──────────────────────────────────────────────
# Рендер: ASCII
# ──────────────────────────────────────────────

def render_ascii(world: World) -> None:
    occupied = {(o.x, o.y) for o in world.organisms}
    lines = []
    for y in range(world.height):
        row = []
        for x in range(world.width):
            if (x, y) in occupied:
                row.append("@")
            elif world.food[y][x] > 15:
                row.append("*")
            elif world.food[y][x] > 0:
                row.append("·")
            else:
                row.append(" ")
        lines.append("".join(row))

    s = world.stats()
    print("\033[H\033[J", end="")  # clear
    print(f"тик {world.tick_n:6d}  "
          f"организмов {s['count']:4d}  "
          f"скор {s['avg_speed']:.2f}  "
          f"восприятие {s['avg_perception']:.2f}  "
          f"размер {s['avg_size']:.2f}")
    print("┌" + "─" * world.width + "┐")
    for line in lines:
        print("│" + line + "│")
    print("└" + "─" * world.width + "┘")
    print("Ctrl+C для выхода")


# ──────────────────────────────────────────────
# Рендер: pygame
# ──────────────────────────────────────────────

CELL = 10  # пикселей на клетку

def render_pygame(world: World, screen, font) -> None:
    import pygame

    occupied = {(o.x, o.y): o for o in world.organisms}
    screen.fill((15, 15, 20))

    for y in range(world.height):
        for x in range(world.width):
            if (x, y) in occupied:
                org = occupied[(x, y)]
                # цвет зависит от скорости генома
                r = min(255, int(50 + org.genome.speed * 60))
                g = min(255, int(200 - org.genome.size * 40))
                b = min(255, int(org.genome.perception * 25))
                pygame.draw.rect(screen, (r, g, b),
                                 (x * CELL, y * CELL + 30, CELL - 1, CELL - 1))
            elif world.food[y][x] > 0:
                intensity = int(world.food[y][x] / FOOD_MAX_ENERGY * 180)
                pygame.draw.rect(screen, (0, intensity, 0),
                                 (x * CELL, y * CELL + 30, CELL - 1, CELL - 1))

    s = world.stats()
    text = (f"тик {world.tick_n}  "
            f"орг: {s['count']}  "
            f"скор: {s['avg_speed']:.2f}  "
            f"восприятие: {s['avg_perception']:.2f}  "
            f"размер: {s['avg_size']:.2f}")
    surf = font.render(text, True, (200, 200, 200))
    screen.blit(surf, (5, 5))

    pygame.display.flip()


# ──────────────────────────────────────────────
# Точка входа
# ──────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Цифровая жизнь")
    parser.add_argument("--width",  type=int,   default=80)
    parser.add_argument("--height", type=int,   default=40)
    parser.add_argument("--seed",   type=int,   default=30,  help="начальных организмов")
    parser.add_argument("--fps",    type=int,   default=20)
    parser.add_argument("--ascii",  action="store_true",     help="ASCII режим")
    args = parser.parse_args()

    world = World(args.width, args.height)

    # засеяем мир едой
    for y in range(world.height):
        for x in range(world.width):
            if random.random() < 0.15:
                world.food[y][x] = random.uniform(5.0, FOOD_MAX_ENERGY)

    # первые организмы
    for _ in range(args.seed):
        world.organisms.append(Organism(
            x      = random.randrange(world.width),
            y      = random.randrange(world.height),
            genome = Genome.random(),
        ))

    if args.ascii:
        try:
            while True:
                world.tick()
                render_ascii(world)
                time.sleep(1 / args.fps)
                if not world.organisms:
                    print("Все вымерли. Перезапуск...")
                    time.sleep(2)
                    break
        except KeyboardInterrupt:
            print("\nВыход.")
        return

    # pygame режим
    try:
        import pygame
    except ImportError:
        print("pygame не установлен. Используй: pip install pygame")
        print("Или запусти с флагом --ascii")
        sys.exit(1)

    pygame.init()
    screen = pygame.display.set_mode((args.width * CELL, args.height * CELL + 30))
    pygame.display.set_caption("artificial-life")
    font  = pygame.font.SysFont("monospace", 13)
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        world.tick()
        render_pygame(world, screen, font)
        clock.tick(args.fps)

        if not world.organisms:
            time.sleep(1)
            # засеем снова
            for _ in range(args.seed):
                world.organisms.append(Organism(
                    x=random.randrange(world.width),
                    y=random.randrange(world.height),
                    genome=Genome.random(),
                ))

    pygame.quit()


if __name__ == "__main__":
    main()
