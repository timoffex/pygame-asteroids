"""Defines the AsteroidGeneratorFactory and AsteroidFactory for spawning
asteroids in the game.

"""

import random

import pygame

import game_objects
from game_objects import GameObject

from extra_bullets import ExtraBulletFactory
from extra_heart import ExtraHeartFactory
from game_object_coroutine import GameObjectCoroutine, resume_after
from game_time import GameTime
from hittable import Hittable
from physics import PhysicsSystem, Collision
from player import Player
from rendering import RenderingSystem
from transform import Transform
from utils import first_where


class AsteroidFactory:

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        physics_system: PhysicsSystem,
        rendering_system: RenderingSystem,
        explosion_factory: "_ExplosionFactory",
        provide_asteroid_images,
        extra_heart_factory: ExtraHeartFactory,
        extra_bullet_factory: ExtraBulletFactory,
    ):
        self._physics_system = physics_system
        self._rendering_system = rendering_system
        self._explosion_factory = explosion_factory
        self._provide_asteroid_images = provide_asteroid_images
        self._extra_heart_factory = extra_heart_factory
        self._extra_bullet_factory = extra_bullet_factory

    def __call__(
        self,
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
        self._rendering_system.new_sprite(
            game_object,
            pygame.transform.scale(
                random.choice(self._provide_asteroid_images()), (50, 50)
            ),
            transform,
        )

        # Physics body with a circle collider
        body = self._physics_system.new_body(
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
            def __init__(
                self,
                explosion_factory,
                extra_heart_factory,
                extra_bullet_factory,
            ):
                self._num_hits = 0
                self._explosion_factory = explosion_factory
                self._extra_heart_factory = extra_heart_factory
                self._extra_bullet_factory = extra_bullet_factory
                self._is_destroyed = False

            def hit(self):
                if self._is_destroyed:
                    return

                self._num_hits += 1

                if self._num_hits >= 10:
                    self._is_destroyed = True
                    game_object.destroy()
                    self._explosion_factory(x=transform.x, y=transform.y)
                    counter.increment()

                    if random.uniform(0, 1) < 0.2:
                        self._extra_heart_factory(x=transform.x, y=transform.y)
                    elif random.uniform(0, 1) < 0.5:
                        self._extra_bullet_factory(
                            x=transform.x, y=transform.y, amount=30
                        )

        body.add_data(
            AsteroidHittable(
                self._explosion_factory,
                self._extra_heart_factory,
                self._extra_bullet_factory,
            )
        )

        return game_object


class AsteroidGeneratorFactory:

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        game_time: GameTime,
        asteroid_factory: AsteroidFactory,
    ):
        self._time = game_time
        self._asteroid_factory = asteroid_factory

    def __call__(
        self,
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
                self._asteroid_factory(
                    counter,
                    x=random.uniform(x, x + width),
                    y=random.uniform(y, y + height),
                    vx=random.gauss(0, 0.03),
                    vy=random.gauss(0, 0.03),
                )
                yield resume_after(time=self._time, delay_ms=interval_ms)

        GameObjectCoroutine(game_object, generate_asteroids()).start()

        return game_object


class _ExplosionFactory:

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        rendering_system: RenderingSystem,
        game_time: GameTime,
        provide_explosion_images,
    ):
        self._rendering_system = rendering_system
        self._game_time = game_time
        self._provide_explosion_images = provide_explosion_images

    def __call__(self, x: float, y: float):
        game_object = game_objects.new_object()
        transform = Transform()
        transform.set_local_x(x)
        transform.set_local_y(y)

        explosion_images = self._provide_explosion_images()

        def animation():
            for i in range(25):
                sprite = self._rendering_system.new_sprite(
                    game_object, explosion_images[i], transform
                )
                yield resume_after(self._game_time, delay_ms=20)
                sprite.destroy()
            game_object.destroy()

        GameObjectCoroutine(game_object, animation()).start()
