"""This module defines a factory to spawn collectable ammo drops."""

import pygame

from collectable_item import make_collectable_item
from player import Player


_extra_bullets_image = pygame.image.load(
    "images/bullet_drop.png"
).convert_alpha()


def make_ammo_container(x: float, y: float, amount: int):
    """Spawns a bullet container at (x, y) with the given number of
    bullets.

    """

    def player_collect(player: Player):
        player.bullets += amount

    make_collectable_item(
        x=x,
        y=y,
        image=_extra_bullets_image,
        trigger_radius=16,
        player_collect=player_collect,
    )
