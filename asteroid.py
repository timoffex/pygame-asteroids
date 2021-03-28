import pinject
import pygame
import random

from extra_heart import ExtraHeartFactory
from game_object import GameObject, GameObjectSystem
from game_object_coroutine import GameObjectCoroutine, resume_after
from game_time import GameTime
from hittable import Hittable
from physics import PhysicsSystem, Collision
from player import Player
from rendering import RenderingSystem
from transform import Transform
from utils import first_where


class ExplosionFactory:
    @pinject.copy_args_to_internal_fields
    def __init__(
        self,
        game_object_system,
        rendering_system,
        game_time,
        provide_explosion_images,
    ):
        self._game_object_system: GameObjectSystem
        self._rendering_system: RenderingSystem
        self._game_time: GameTime
        pass

    def __call__(self, x: float, y: float):
        go = self._game_object_system.new_object()
        transform = Transform()
        transform.set_local_x(x)
        transform.set_local_y(y)

        explosion_images = self._provide_explosion_images()

        def animation():
            for n in range(25):
                sprite = self._rendering_system.new_sprite(
                    go, explosion_images[n], transform
                )
                yield resume_after(self._game_time, delay_ms=20)
                sprite.destroy()
            go.destroy()

        GameObjectCoroutine(go, animation()).start()


class AsteroidFactory:
    def __init__(
        self,
        game_object_system: GameObjectSystem,
        physics_system: PhysicsSystem,
        rendering_system: RenderingSystem,
        explosion_factory: ExplosionFactory,
        provide_asteroid_images,
        extra_heart_factory: ExtraHeartFactory,
    ):
        self._game_object_system = game_object_system
        self._physics_system = physics_system
        self._rendering_system = rendering_system
        self._explosion_factory = explosion_factory
        self._provide_asteroid_images = provide_asteroid_images
        self._extra_heart_factory = extra_heart_factory
        pass

    def __call__(
        self,
        counter,
        *,
        x: float = 400,
        y: float = 300,
        vx: float = 0,
        vy: float = 0
    ) -> GameObject:
        go = self._game_object_system.new_object()

        img = pygame.transform.scale(
            random.choice(self._provide_asteroid_images()), (50, 50)
        )

        transform = Transform()
        self._rendering_system.new_sprite(go, img, transform)
        body = self._physics_system.new_body(
            game_object=go, transform=transform, mass=5
        )
        body.add_circle_collider(radius=25)

        def on_collision(collision: Collision):
            player = first_where(
                lambda x: isinstance(x, Player),
                collision.body_other.get_data(),
            )

            if player:
                player.decrement_hearts()

        body.add_collision_hook(on_collision)

        transform.set_local_x(x)
        transform.set_local_y(y)
        body.velocity_x = vx
        body.velocity_y = vy

        class AsteroidHittable(Hittable):
            def __init__(self, explosion_factory, extra_heart_factory):
                self._num_hits = 0
                self._explosion_factory = explosion_factory
                self._extra_heart_factory = extra_heart_factory
                self._is_destroyed = False

            def hit(self):
                if self._is_destroyed:
                    return

                self._num_hits += 1

                if self._num_hits >= 10:
                    self._is_destroyed = True
                    go.destroy()
                    self._explosion_factory(x=transform.x(), y=transform.y())
                    counter.increment()

                    if random.uniform(0, 1) < 0.2:
                        self._extra_heart_factory(
                            x=transform.x(), y=transform.y()
                        )

        body.add_data(
            AsteroidHittable(
                self._explosion_factory, self._extra_heart_factory
            )
        )

        return go


class AsteroidGeneratorFactory:
    def __init__(
        self,
        game_object_system: GameObjectSystem,
        game_time: GameTime,
        asteroid_factory: AsteroidFactory,
    ):
        self._game_objects = game_object_system
        self._time = game_time
        self._asteroid_factory = asteroid_factory

    def __call__(
        self,
        counter,
        x: float,
        y: float,
        width: float,
        height: float,
        interval_ms: float,
    ) -> GameObject:
        go = self._game_objects.new_object()

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

        GameObjectCoroutine(go, generate_asteroids()).start()

        return go
