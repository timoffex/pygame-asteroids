"""This module defines a factory to spawn collectable heart containers."""

from collectable_item import CollectableItemFactory
from player import Player


class ExtraHeartFactory:
    """A factory that spawns collectable heart items that restore the player's
    hearts.

    """

    # pylint: disable=too-few-public-methods
    # This has to be a class to be injectable with Pinject.

    def __init__(
        self,
        collectable_item_factory: CollectableItemFactory,
        provide_extra_heart_image,
    ):
        self._collectable_item_factory = collectable_item_factory
        self._provide_extra_heart_image = provide_extra_heart_image

    def __call__(self, x: float, y: float):
        """Spawns a heart container at (x, y)."""

        def player_collect(player: Player):
            player.increment_hearts()

        self._collectable_item_factory(
            x=x,
            y=y,
            image=self._provide_extra_heart_image(),
            trigger_radius=16,
            player_collect=player_collect,
        )
