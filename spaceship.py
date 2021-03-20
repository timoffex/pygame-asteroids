import math
import pygame

from game_env import GameEnv
from game_object import GameObject
from game_object_coroutine import GameObjectCoroutine, resume_after
from hittable import Hittable
from transform import Transform
from physics import PhysicsBody, Collision, add_physics_component
from rendering import add_sprite_component


def make_bullet(
    game: GameEnv,
    *,
    x: float,
    y: float,
    angle: float,
    vx: float = 0,
    vy: float = 0,
    lifetime_ms: float = 10000
) -> GameObject:
    go = game.game_objects.new_object()

    img = pygame.transform.scale(
        pygame.image.load("images/asteroid.png").convert_alpha(), (5, 5)
    )

    transform = Transform()
    transform.set_local_x(x)
    transform.set_local_y(y)
    transform.set_local_angle(angle)

    add_sprite_component(go, game.graphics.new_sprite(img, transform))

    body = game.physics.new_circle_body(
        transform=transform, radius=2.5, mass=0.1
    )
    add_physics_component(go, body)

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
            print("Bullet hit something hittable!", go)
            hittable.hit()
            go.destroy()

    body.add_collision_hook(on_collision)

    def destroy_after_lifetime():
        yield resume_after(game.time, delay_ms=lifetime_ms)
        go.destroy()

    GameObjectCoroutine(go, destroy_after_lifetime()).start()

    return go


class Guns:
    def __init__(
        self,
        game: GameEnv,
        *,
        shooting_transform: Transform,
        shooting_body: PhysicsBody,
        firing_delay_ms: float
    ):
        self._game = game
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
        make_bullet(
            self._game,
            x=self._shooting_transform.x(),
            y=self._shooting_transform.y(),
            angle=self._shooting_transform.angle(),
            vx=self._shooting_body.velocity_x,
            vy=self._shooting_body.velocity_y,
        )


def make_spaceship(game: GameEnv, x: float = 0, y: float = 0) -> GameObject:
    go = game.game_objects.new_object()

    img = pygame.transform.rotate(
        pygame.transform.scale(
            pygame.image.load("images/spaceship.png").convert_alpha(), (50, 50)
        ),
        -90,
    )

    transform = Transform()
    transform.set_local_x(x)
    transform.set_local_y(y)
    sprite = game.graphics.new_sprite(img, transform)
    body = game.physics.new_circle_body(transform=transform, radius=25, mass=1)

    # Register the sprite and physics body as components so that they
    # get disabled when the object is destroyed
    add_physics_component(go, body)
    add_sprite_component(go, sprite)

    guns = Guns(
        game,
        shooting_transform=transform,
        shooting_body=body,
        firing_delay_ms=50,
    )

    def update(delta_time: float) -> None:
        if game.inputs.is_key_down(pygame.K_d):
            transform.rotate(-delta_time / 100)
        if game.inputs.is_key_down(pygame.K_a):
            transform.rotate(delta_time / 100)

        if game.inputs.is_key_down(pygame.K_s):
            # Slow down gradually
            body.velocity_x *= math.pow(0.8, delta_time / 50)
            body.velocity_y *= math.pow(0.8, delta_time / 50)

        if game.inputs.is_key_down(pygame.K_w):
            # Speed up in the direction the ship is facing

            s = math.sin(transform.angle())
            c = math.cos(transform.angle())
            body.velocity_x += delta_time * c / 1000
            body.velocity_y -= delta_time * s / 1000

        if game.inputs.is_key_down(pygame.K_SPACE) and guns.is_ready_to_fire():
            guns.fire()

    go.add_update_hook(update)
    return go
