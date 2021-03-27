import math
import pinject
import pygame

from game_object import GameObject, GameObjectSystem
from game_object_coroutine import GameObjectCoroutine, resume_after
from game_time import GameTime
from hittable import Hittable
from inputs import Inputs
from transform import Transform
from physics import PhysicsSystem, PhysicsBody, Collision
from rendering import RenderingSystem


class BulletFactory:
    def __init__(
        self,
        game_time: GameTime,
        physics_system: PhysicsSystem,
        rendering_system: RenderingSystem,
        game_object_system: GameObjectSystem,
        provide_asteroid_images,
    ):
        self._game_time = game_time
        self._physics_system = physics_system
        self._rendering_system = rendering_system
        self._game_object_system = game_object_system
        self._provide_asteroid_images = provide_asteroid_images
        pass

    def __call__(
        self,
        *,
        x: float,
        y: float,
        angle: float,
        vx: float = 0,
        vy: float = 0,
        lifetime_ms: float = 10000
    ) -> GameObject:
        go = self._game_object_system.new_object()

        img = pygame.transform.scale(self._provide_asteroid_images()[0], (5, 5))

        transform = Transform()
        transform.set_local_x(x)
        transform.set_local_y(y)
        transform.set_local_angle(angle)

        self._rendering_system.new_sprite(go, img, transform)

        body = self._physics_system.new_circle_body(
            game_object=go, transform=transform, radius=2.5, mass=0.1
        )

        speed = 0.1
        body.velocity_x = vx + speed * math.cos(angle)
        body.velocity_y = vy - speed * math.sin(angle)

        def on_collision(collision: Collision):
            hittable: Hittable
            hittable = next(
                (
                    x
                    for x in collision.body_other.get_data()
                    if isinstance(x, Hittable)
                ),
                None,
            )

            if hittable:
                hittable.hit()
                go.destroy()

        body.add_collision_hook(on_collision)

        def destroy_after_lifetime():
            yield resume_after(self._game_time, delay_ms=lifetime_ms)
            go.destroy()

        GameObjectCoroutine(go, destroy_after_lifetime()).start()

        return go


class Guns:
    def __init__(
        self,
        bullet_factory: BulletFactory,
        shooting_transform: Transform,
        shooting_body: PhysicsBody,
        firing_delay_ms: float,
    ):
        self._bullet_factory = bullet_factory
        self._shooting_transform = shooting_transform
        self._shooting_body = shooting_body
        self._last_shot_time = -math.inf
        self._firing_delay_ms = firing_delay_ms

    def is_ready_to_fire(self):
        return (
            pygame.time.get_ticks()
            > self._last_shot_time + self._firing_delay_ms
        )

    def fire(self):
        self._last_shot_time = pygame.time.get_ticks()
        self._bullet_factory(
            x=self._shooting_transform.x(),
            y=self._shooting_transform.y(),
            angle=self._shooting_transform.angle(),
            vx=self._shooting_body.velocity_x,
            vy=self._shooting_body.velocity_y,
        )


class GunsFactory:
    @pinject.copy_args_to_internal_fields
    def __init__(self, bullet_factory: BulletFactory):
        pass

    def __call__(
        self,
        shooting_transform: Transform,
        shooting_body: PhysicsBody,
        firing_delay_ms: float,
    ) -> Guns:
        return Guns(
            bullet_factory=self._bullet_factory,
            shooting_transform=shooting_transform,
            shooting_body=shooting_body,
            firing_delay_ms=firing_delay_ms,
        )


class SpaceshipFactory:
    def __init__(
        self,
        inputs: Inputs,
        game_object_system: GameObjectSystem,
        rendering_system: RenderingSystem,
        physics_system: PhysicsSystem,
        guns_factory: GunsFactory,
    ):
        self._inputs = inputs
        self._game_object_system = game_object_system
        self._rendering_system = rendering_system
        self._physics_system = physics_system
        self._guns_factory = guns_factory
        pass

    def __call__(self, x: float = 0, y: float = 0) -> GameObject:
        go = self._game_object_system.new_object()

        img = pygame.transform.rotate(
            pygame.transform.scale(
                pygame.image.load("images/spaceship.png").convert_alpha(),
                (50, 50),
            ),
            -90,
        )

        transform = Transform()
        transform.set_local_x(x)
        transform.set_local_y(y)
        self._rendering_system.new_sprite(go, img, transform)
        body = self._physics_system.new_circle_body(
            game_object=go, transform=transform, radius=25, mass=1
        )

        guns = self._guns_factory(
            shooting_transform=transform,
            shooting_body=body,
            firing_delay_ms=20,
        )

        def update(delta_time: float) -> None:
            if self._inputs.is_key_down(pygame.K_d):
                transform.rotate(-delta_time / 100)
            if self._inputs.is_key_down(pygame.K_a):
                transform.rotate(delta_time / 100)

            if self._inputs.is_key_down(pygame.K_s):
                # Slow down gradually
                body.velocity_x *= math.pow(0.8, delta_time / 50)
                body.velocity_y *= math.pow(0.8, delta_time / 50)

            if self._inputs.is_key_down(pygame.K_w):
                # Speed up in the direction the ship is facing

                s = math.sin(transform.angle())
                c = math.cos(transform.angle())
                body.velocity_x += delta_time * c / 1000
                body.velocity_y -= delta_time * s / 1000

            if (
                self._inputs.is_key_down(pygame.K_SPACE)
                and guns.is_ready_to_fire()
            ):
                guns.fire()

        go.add_update_hook(update)
        return go
