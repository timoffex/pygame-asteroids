import math
import random

import pygame

from bullet import Bullet
import game_objects
from game_objects import GameObject
from game_object_coroutine import GameObjectCoroutine, resume_after
import graphics
import inputs
import physics
from physics import PhysicsBody

from transform import Transform
from player import Player


_spaceship_idle_image = pygame.transform.scale(
    pygame.image.load("images/spaceship_idle.png").convert_alpha(),
    (50, 50),
)

_spaceship_invincible_image = pygame.transform.scale(
    pygame.image.load("images/spaceship_invincible.png").convert_alpha(),
    (50, 50),
)

_spaceship_moving_image = pygame.transform.scale(
    pygame.image.load("images/spaceship_moving.png").convert_alpha(),
    (50, 50),
)


class Spaceship:
    def __init__(
        self, player: Player, game_object: GameObject, sprite: graphics.Sprite
    ):
        self._player = player
        self._game_object = game_object
        self._sprite = sprite
        self._invincibility_ms = 500
        self._is_invincible = False

    def get_hit_by_asteroid(self):
        """Hit the spaceship with an asteroid."""

        if not self.is_invincible:
            self._player.decrement_hearts()
            GameObjectCoroutine(
                self._game_object, self._become_invincible()
            ).start()

    def destroy(self):
        """Destroys the spaceship."""

        self._game_object.destroy()

    @property
    def is_invincible(self):
        """Whether the spaceship is currently invincible because it recently
        took damage.

        """
        return self._is_invincible

    def _become_invincible(self):
        self._is_invincible = True
        self._sprite.surface = _spaceship_invincible_image

        yield resume_after(self._invincibility_ms)

        self._is_invincible = False
        self._sprite.surface = _spaceship_idle_image


def make_spaceship(
    player: Player,
    x: float = 0,
    y: float = 0,
) -> Spaceship:
    go = game_objects.new_object()

    transform = Transform()
    transform.set_local_x(x)
    transform.set_local_y(y)

    sprite = graphics.new_sprite(go, _spaceship_idle_image, transform)

    body = physics.new_body(game_object=go, transform=transform, mass=1)
    body.add_circle_collider(radius=25)

    spaceship = Spaceship(player=player, game_object=go, sprite=sprite)
    body.add_data(spaceship)
    body.add_data(player)

    guns_transform = Transform(parent=transform)
    guns_transform.set_local_x(40)
    guns = _Guns(
        player=player,
        shooting_transform=guns_transform,
        shooting_body=body,
        firing_delay_ms=100,
    )

    def update(delta_time: float) -> None:
        nonlocal sprite

        if inputs.is_key_down(pygame.K_d):
            transform.rotate(-delta_time / 100)
        if inputs.is_key_down(pygame.K_a):
            transform.rotate(delta_time / 100)

        if inputs.is_key_down(pygame.K_s):
            # Slow down gradually
            body.velocity_x *= math.pow(0.8, delta_time / 50)
            body.velocity_y *= math.pow(0.8, delta_time / 50)

        if inputs.is_key_down(pygame.K_w):
            # Speed up in the direction the ship is facing

            s = math.sin(transform.angle)
            c = math.cos(transform.angle)
            body.velocity_x += delta_time * c / 1000
            body.velocity_y -= delta_time * s / 1000

            if not spaceship.is_invincible:
                sprite.surface = _spaceship_moving_image
        else:
            if not spaceship.is_invincible:
                sprite.surface = _spaceship_idle_image

        if inputs.is_key_down(pygame.K_SPACE) and guns.is_ready_to_fire():
            guns.fire()

    go.on_update(update)
    return spaceship


class _Guns:
    def __init__(
        self,
        shooting_transform: Transform,
        shooting_body: PhysicsBody,
        firing_delay_ms: float,
        player: Player,
    ):
        self._shooting_transform = shooting_transform
        self._shooting_body = shooting_body
        self._last_shot_time = -math.inf
        self._firing_delay_ms = firing_delay_ms
        self._player = player

    def is_ready_to_fire(self):
        return (
            pygame.time.get_ticks()
            > self._last_shot_time + self._firing_delay_ms
            and self._player.bullets > 0
        )

    def fire(self):
        self._last_shot_time = pygame.time.get_ticks()

        if self._player.bullets > 0:
            self._player.bullets -= 1
            bullet = Bullet(
                x=self._shooting_transform.x,
                y=self._shooting_transform.y,
                angle=self._shooting_transform.angle,
                speed=self._shooting_body.speed + 0.1,
                lifetime_ms=30000,
            )

            if random.uniform(0, 1) < 0.05:
                bullet.superpower(
                    angle=self._shooting_transform.angle,
                    speed=self._shooting_body.speed + 0.5,
                )
