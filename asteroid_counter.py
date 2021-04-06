"""This module defines the on-screen asteroid counter."""

import pygame

import game_objects
import graphics
from transform import Transform


_count = 0


def increment():
    """Increments the asteroid counter."""
    global _count
    _count += 1
    _text.text = str(_count)


_transform = Transform()
_transform.set_local_x(400)
_transform.set_local_y(20)

_text: graphics.Text = graphics.new_text(
    game_object=game_objects.new_object(),
    transform=_transform,
    font=pygame.font.Font(None, 36),
    text=str(_count),
)
