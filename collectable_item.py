"""This module helps create collectable items."""

from dataclasses import dataclass
from typing import Callable

import pygame

import game_objects
from game_objects import GameObject

import graphics
from graphics import Sprite

from physics import PhysicsSystem, TriggerCollider, TriggerEvent
from player import Player
from transform import Transform
from utils import first_where


@dataclass
class CollectableItem:
    """The data for a collectable item."""

    game_object: GameObject
    transform: Transform
    sprite: Sprite
    trigger_zone: TriggerCollider


class CollectableItemFactory:
    """A factory that can constructs CollectableItems."""

    # pylint: disable=too-few-public-methods
    # This has to be a class to be injectable with Pinject.

    def __init__(self, physics_system: PhysicsSystem):
        self._physics_system = physics_system

    def __call__(
        self,
        *,
        x: float,
        y: float,
        image: pygame.Surface,
        trigger_radius: float,
        player_collect: Callable[[Player], None],
    ) -> CollectableItem:
        """Creates a CollectableItem at the specified position.

        When a player enters the collectable item, the
        ``player_collect`` function is called and the item is
        destroyed.
        """

        game_object = game_objects.new_object()
        transform = Transform()
        transform.set_local_x(x)
        transform.set_local_y(y)

        sprite = graphics.new_sprite(
            game_object=game_object,
            surface=image,
            transform=transform,
        )

        trigger_zone = self._physics_system.new_circle_trigger(
            radius=trigger_radius,
            game_object=game_object,
            transform=transform,
        )

        is_collected = False

        def handle_trigger_enter(trigger_event: TriggerEvent):
            nonlocal is_collected

            if is_collected:
                return

            player = first_where(
                lambda x: isinstance(x, Player),
                trigger_event.other_collider.get_data(),
            )

            if player:
                is_collected = True
                player_collect(player)
                game_object.destroy()

        trigger_zone.on_trigger_enter(handle_trigger_enter)

        return CollectableItem(
            game_object=game_object,
            transform=transform,
            sprite=sprite,
            trigger_zone=trigger_zone,
        )
