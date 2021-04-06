"""This module defines a factory to spawn collectable ammo drops."""

from collectable_item import make_collectable_item
from player import Player


class ExtraBulletFactory:
    """A factory that spawns collectable containers of extra ammo."""

    # pylint: disable=too-few-public-methods
    # This has to be a class to be injectable with Pinject.

    def __init__(self, provide_extra_bullets_image):
        self._provide_extra_bullets_image = provide_extra_bullets_image

    def __call__(self, x: float, y: float, amount: int):
        """Spawns a bullet container at (x, y) with the given number of
        bullets.

        """

        def player_collect(player: Player):
            player.bullets += amount

        make_collectable_item(
            x=x,
            y=y,
            image=self._provide_extra_bullets_image(),
            trigger_radius=16,
            player_collect=player_collect,
        )
