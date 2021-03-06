"""This module defines higher level graphics abstractions on top of pygame.

The module should be imported using ``import graphics``, but types may be
imported individually using ``from graphics import ...``. The following
module-level functions are provided:

  graphics.new_sprite(game_object, surface, transform)
  graphics.new_text(game_object, transform, font, text)
  graphics.render(screen)

"""

import math
from abc import ABC, abstractmethod

import pygame

from game_objects import GameObject
from transform import Transform


class GraphicalObject(ABC):
    """Base class for all graphical objects."""

    # pylint: disable=too-few-public-methods

    def __init__(self, game_object: GameObject):
        self.__game_object = game_object

        self.__is_destroyed = False
        self.__remove_destroy_hook = game_object.on_destroy(self.destroy)

    def destroy(self):
        """Removes this graphical object causing it to no longer be drawn."""

        if self.__is_destroyed:
            return

        self.__is_destroyed = True
        self.__remove_destroy_hook()
        _discard_graphical_object(self)


class Sprite(GraphicalObject):
    """A 2D image attached to a GameObject that moves and rotates
    according to a Transform.

    Create Sprites using ``new_sprite``.
    """

    @property
    @abstractmethod
    def surface(self) -> pygame.Surface:
        """The surface (image) that this sprite is drawing."""

    @surface.setter
    @abstractmethod
    def surface(self, new_value: pygame.Surface):
        pass


class Text(GraphicalObject):
    """A string of text that is rendered on the screen and can be positioned
    according to a Transform.

    Create Texts using ``new_text``.
    """

    @property
    @abstractmethod
    def text(self) -> str:
        """The text that this displays."""

    @text.setter
    @abstractmethod
    def text(self, new_value: str):
        pass

    @property
    @abstractmethod
    def font(self) -> pygame.font.Font:
        """The font used to draw the text."""

    @font.setter
    @abstractmethod
    def font(self, new_value: pygame.font.Font):
        pass

    @property
    @abstractmethod
    def color(self) -> pygame.Color:
        """The color used to draw the text."""

    @color.setter
    @abstractmethod
    def color(self, new_value: pygame.Color):
        pass


def new_sprite(
    game_object: GameObject,
    surface: pygame.Surface,
    transform: Transform,
) -> Sprite:
    """Creates and returns a new Sprite."""

    sprite = _Sprite(
        game_object=game_object,
        surface=surface,
        transform=transform,
    )
    _graphical_objects.add(sprite)
    return sprite


def new_text(
    game_object: GameObject,
    transform: Transform,
    font: pygame.font.Font,
    text: str,
):
    """Creates and returns a Text object."""

    text = _Text(
        game_object=game_object,
        transform=transform,
        text=text,
        font=font,
    )
    _graphical_objects.add(text)
    return text


def render(screen: pygame.Surface):
    """Renders all created graphical objects on the screen."""
    for obj in _graphical_objects:
        obj.render(screen)


def _discard_graphical_object(obj):
    _graphical_objects.discard(obj)


_graphical_objects: set["_GraphicalObject"] = set()


class _GraphicalObject(GraphicalObject):
    @abstractmethod
    def render(self, screen: pygame.Surface):
        """Renders this object to the given surface."""


class _Sprite(_GraphicalObject, Sprite):
    def __init__(
        self,
        surface: pygame.Surface,
        transform: Transform,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._surface = surface
        self._transform = transform

    @property
    def surface(self):
        return self._surface

    @surface.setter
    def surface(self, new_value):
        self._surface = new_value

    def render(self, screen: pygame.Surface):
        x = self._transform.x
        y = self._transform.y
        img_rotated = pygame.transform.rotate(
            self._surface, self._transform.angle * 180 / math.pi
        )

        off_x = (
            self._surface.get_rect().centerx
            - img_rotated.get_rect().centerx
            - self._surface.get_rect().width / 2
        )
        off_y = (
            self._surface.get_rect().centery
            - img_rotated.get_rect().centery
            - self._surface.get_rect().height / 2
        )

        screen.blit(img_rotated, (x + off_x, y + off_y))


class _Text(_GraphicalObject, Text):
    def __init__(
        self,
        transform: Transform,
        text: str,
        font: pygame.font.Font,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._transform = transform

        self._font = font
        self._text = text
        self._rendered_text = None
        self._needs_update = True
        self._color = pygame.Color(255, 255, 255)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_value):
        if new_value != self._text:
            self._text = new_value
            self._needs_update = True

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, new_value):
        if new_value != self._font:
            self._font = new_value
            self._needs_update = True

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, new_value):
        if new_value != self._color:
            self._color = new_value
            self._needs_update = True

    def render(self, screen: pygame.Surface):
        if self._needs_update:
            self._needs_update = False
            self._rendered_text = self._font.render(
                self._text, False, self._color
            )

        screen.blit(
            self._rendered_text,
            (self._transform.x, self._transform.y),
        )
