import random

import pygame

import game_objects
from game_objects import GameObject
import graphics
import physics
from physics import Collision

from extra_bullets import make_ammo_container
from extra_heart import make_extra_heart
from game_object_coroutine import GameObjectCoroutine, resume_after
from hittable import Hittable
from player import Player
from transform import Transform
from utils import first_where


_asteroid_images = [pygame.image.load("images/asteroid.png").convert_alpha()]


def make_asteroid(
    counter,
    *,
    x: float = 400,
    y: float = 300,
    vx: float = 0,
    vy: float = 0,
) -> GameObject:
    game_object = game_objects.new_object()

    transform = Transform()
    transform.set_local_x(x)
    transform.set_local_y(y)

    # Sprite
    graphics.new_sprite(
        game_object,
        pygame.transform.scale(random.choice(_asteroid_images), (50, 50)),
        transform,
    )

    # Physics body with a circle collider
    body = physics.new_body(
        game_object=game_object, transform=transform, mass=5
    )
    body.add_circle_collider(radius=25)

    # Collision hook to damage player
    def on_collision(collision: Collision):
        player = first_where(
            lambda x: isinstance(x, Player),
            collision.body_other.get_data(),
        )

        if player:
            player.decrement_hearts()

    body.add_collision_hook(on_collision)
    body.velocity_x = vx
    body.velocity_y = vy

    # Asteroids are Hittable
    class AsteroidHittable(Hittable):
        def __init__(self):
            self._num_hits = 0
            self._is_destroyed = False

        def hit(self):
            if self._is_destroyed:
                return

            self._num_hits += 1

            if self._num_hits >= 10:
                self._is_destroyed = True
                game_object.destroy()
                _make_explosion(x=transform.x, y=transform.y)
                counter.increment()

                if random.uniform(0, 1) < 0.2:
                    make_extra_heart(x=transform.x, y=transform.y)
                elif random.uniform(0, 1) < 0.5:
                    make_ammo_container(
                        x=transform.x, y=transform.y, amount=30
                    )

    body.add_data(AsteroidHittable())

    return game_object


def make_asteroid_generator(
    *,
    counter,
    x: float,
    y: float,
    width: float,
    height: float,
    interval_ms: float,
) -> GameObject:
    game_object = game_objects.new_object()

    def generate_asteroids():
        while True:
            make_asteroid(
                counter,
                x=random.uniform(x, x + width),
                y=random.uniform(y, y + height),
                vx=random.gauss(0, 0.03),
                vy=random.gauss(0, 0.03),
            )
            yield resume_after(delay_ms=interval_ms)

    GameObjectCoroutine(game_object, generate_asteroids()).start()

    return game_object


_explosion_images = [
    pygame.image.load(f"images/explosion_{n}.png").convert_alpha()
    for n in range(25)
]


def _make_explosion(x: float, y: float):
    game_object = game_objects.new_object()
    transform = Transform()
    transform.set_local_x(x)
    transform.set_local_y(y)

    def animation():
        for i in range(25):
            sprite = graphics.new_sprite(
                game_object, _explosion_images[i], transform
            )
            yield resume_after(delay_ms=20)
            sprite.destroy()
        game_object.destroy()

    GameObjectCoroutine(game_object, animation()).start()
