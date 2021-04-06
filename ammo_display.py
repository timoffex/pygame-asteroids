import pygame

from game_objects import GameObject
import graphics

from player import Player
from transform import Transform


class AmmoDisplay:
    def __init__(
        self,
        *,
        player: Player,
        transform: Transform,
        game_object: GameObject,
    ):
        self._player = player
        self._transform = transform
        self._game_object = game_object
        self._ammo_image = pygame.transform.scale(
            pygame.image.load("images/bullet.png").convert_alpha(),
            (40, 40),
        )

        # Destroy self when game object is destroyed
        self._is_destroyed = False
        self._remove_destroy_hook = self._game_object.on_destroy(self.destroy)

        # When bullet amount changes, run _update_amount()
        self._remove_player_listener = self._player.on_bullets_changed(
            self._update_amount
        )

        # Ammo sprite
        self._image_transform = Transform(parent=self._transform)
        self._image_transform.set_local_x(15)
        self._image_transform.set_local_y(10)
        graphics.new_sprite(
            game_object=self._game_object,
            transform=self._image_transform,
            surface=self._ammo_image,
        )

        # Ammo text
        self._text_transform = Transform(parent=self._transform)
        self._text_transform.set_local_x(50)
        self._text = graphics.new_text(
            game_object=self._game_object,
            transform=self._text_transform,
            font=pygame.font.Font(None, 36),
            text=str(self._player.bullets),
        )

    def destroy(self):
        if self._is_destroyed:
            return

        self._is_destroyed = True
        self._remove_destroy_hook()
        self._remove_player_listener()

    def _update_amount(self, new_ammo_amount: int):
        self._text.text = str(new_ammo_amount)
