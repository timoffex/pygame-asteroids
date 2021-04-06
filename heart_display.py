import pygame

import game_objects
from game_objects import GameObject

import graphics

from player import Player
from transform import Transform


_heart_image = pygame.image.load("images/heart.png").convert_alpha()


class HeartDisplay:
    def __init__(
        self,
        player: Player,
        transform: Transform,
        game_object: GameObject,
    ):
        self._player = player
        self._transform = transform
        self._game_object = game_object

        self._is_destroyed = False
        self._remove_destroy_hook = self._game_object.on_destroy(self.destroy)
        self._remove_hearts_hook = self._player.on_hearts_changed(
            self._update_hearts
        )

        self._heart_x_offset = 25
        self._heart_objects: list[GameObject] = []
        self._update_hearts(player.hearts)

    def destroy(self):
        if not self._is_destroyed:
            self._is_destroyed = True

            self._remove_destroy_hook()
            self._remove_hearts_hook()

    def _update_hearts(self, num_hearts: int):
        if num_hearts < len(self._heart_objects):
            for heart in self._heart_objects[num_hearts:]:
                heart.destroy()
            self._heart_objects = self._heart_objects[:num_hearts]
        else:
            for new_heart_idx in range(len(self._heart_objects), num_hearts):
                self._heart_objects.append(self._new_heart(new_heart_idx))

    def _new_heart(self, heart_idx: int) -> GameObject:
        heart_object = game_objects.new_object()

        heart_transform = Transform(parent=self._transform)
        heart_transform.set_local_x(heart_idx * self._heart_x_offset)

        graphics.new_sprite(
            game_object=heart_object,
            surface=_heart_image,
            transform=heart_transform,
        )

        return heart_object
