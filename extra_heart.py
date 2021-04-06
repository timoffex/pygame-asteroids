"""This module defines a factory to spawn collectable heart containers."""

import pygame

from collectable_item import make_collectable_item
from player import Player


_extra_heart_image = pygame.image.load(
    "images/extra_heart.png"
).convert_alpha()


def make_extra_heart(x: float, y: float):
    """Spawns a collectable heart container that restores the
    player's hearts at (x, y).

    """

    def player_collect(player: Player):
        player.increment_hearts()

    make_collectable_item(
        x=x,
        y=y,
        image=_extra_heart_image,
        trigger_radius=16,
        player_collect=player_collect,
    )
