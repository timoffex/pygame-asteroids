"""Defines the bullet, which is what the player shoots at asteroids."""

import math
import random

import pygame

from hittable import Hittable
import game_objects
from game_object_coroutine import (
    GameObjectCoroutine,
    resume_after,
)
import graphics
import physics
from transform import Transform
from utils import first_where


class Bullet:
    """A single bullet.

    This object is added to its physics body and this can be used to
    interact with it after a collision.
    """

    def __init__(
        self,
        *,
        x: float,
        y: float,
        angle: float,
        speed: float,
        lifetime_ms: float = 10000
    ):
        self._is_superpowered = False

        self._game_object = game_objects.new_object()

        img = random.choice(_bullet_images)
        transform = Transform()
        transform.set_local_x(x)
        transform.set_local_y(y)
        transform.set_local_angle(angle)

        self._sprite = graphics.new_sprite(self._game_object, img, transform)

        self._body = physics.new_body(
            game_object=self._game_object, transform=transform, mass=0.8
        )
        self._body.add_circle_collider(radius=7.5)
        self._body.add_data(self)

        self._body.velocity_x = speed * math.cos(angle)
        self._body.velocity_y = -speed * math.sin(angle)
        self._body.add_collision_hook(self._on_collision)

        GameObjectCoroutine(
            self._game_object, self._destroy_after_lifetime(lifetime_ms)
        ).start()

    def superpower(self, *, angle: float, speed: float):
        """Makes the bullet super-powered."""
        self._sprite.surface = _hot_bullet_image
        self._body.velocity_x = speed * math.cos(angle)
        self._body.velocity_y = -speed * math.sin(angle)
        self._is_superpowered = True

    def destroy(self):
        """Destroys the bullet."""
        self._game_object.destroy()

    def _on_collision(self, collision: physics.Collision):
        hittable: Hittable
        hittable = first_where(
            lambda x: isinstance(x, Hittable),
            collision.body_other.get_data(),
        )

        if hittable:
            hittable.hit(hitpoints=5 if self._is_superpowered else 1)
            self.destroy()

    def _destroy_after_lifetime(self, lifetime_ms: float):
        yield resume_after(delay_ms=lifetime_ms)
        self.destroy()


_bullet_images = [pygame.image.load("images/bullet.png").convert_alpha()]
_hot_bullet_image = pygame.image.load("images/hot_bullet.png").convert_alpha()
