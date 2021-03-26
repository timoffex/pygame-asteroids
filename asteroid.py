import pinject
import pygame
import random

from game_object import GameObject, GameObjectSystem
from game_object_coroutine import GameObjectCoroutine, resume_after
from game_time import GameTime
from hittable import Hittable
from physics import PhysicsSystem, add_physics_component
from rendering import RenderingSystem, add_sprite_component
from transform import Transform


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
                    explosion_images[n], transform
                )
                remove_component = add_sprite_component(go, sprite)
                yield resume_after(self._game_time, delay_ms=20)
                remove_component()
                sprite.disable()
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
    ):
        self._game_object_system = game_object_system
        self._physics_system = physics_system
        self._rendering_system = rendering_system
        self._explosion_factory = explosion_factory
        self._provide_asteroid_images = provide_asteroid_images
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
        sprite = self._rendering_system.new_sprite(img, transform)
        body = self._physics_system.new_circle_body(
            transform=transform, radius=25, mass=5
        )

        # Register the sprite and physics body as components so that they
        # get disabled when the object is destroyed
        add_physics_component(go, body)
        add_sprite_component(go, sprite)

        transform.set_local_x(x)
        transform.set_local_y(y)
        body.velocity_x = vx
        body.velocity_y = vy

        class AsteroidHittable(Hittable):
            def __init__(self, explosion_factory):
                self._num_hits = 0
                self._explosion_factory = explosion_factory
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

        body.add_data(AsteroidHittable(self._explosion_factory))

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
