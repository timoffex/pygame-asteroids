import math
import random

import pygame

from bullet import Bullet
import game_objects
from game_objects import GameObject
import graphics
import inputs
import physics
from physics import PhysicsBody

from transform import Transform
from player import Player


def make_spaceship(
    player: Player,
    x: float = 0,
    y: float = 0,
) -> GameObject:
    go = game_objects.new_object()

    img_idle = pygame.transform.scale(
        pygame.image.load("images/spaceship_idle.png").convert_alpha(),
        (50, 50),
    )
    img_moving = pygame.transform.scale(
        pygame.image.load("images/spaceship_moving.png").convert_alpha(),
        (50, 50),
    )

    transform = Transform()
    transform.set_local_x(x)
    transform.set_local_y(y)

    sprite = graphics.new_sprite(go, img_idle, transform)
    is_idle_sprite = True

    body = physics.new_body(game_object=go, transform=transform, mass=1)
    body.add_circle_collider(radius=25)

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
        nonlocal sprite, is_idle_sprite

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

            if is_idle_sprite:
                sprite.destroy()
                sprite = graphics.new_sprite(go, img_moving, transform)
                is_idle_sprite = False
        else:
            if not is_idle_sprite:
                sprite.destroy()
                sprite = graphics.new_sprite(go, img_idle, transform)
                is_idle_sprite = True

        if inputs.is_key_down(pygame.K_SPACE) and guns.is_ready_to_fire():
            guns.fire()

    go.on_update(update)
    return go


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
