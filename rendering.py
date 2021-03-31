"""This module defines higher level graphics abstractions on top of pygame."""

import math
from abc import ABC, abstractmethod
from typing import Callable

import pygame

from game_object import GameObject
from transform import Transform


class GraphicalObject(ABC):
    """Any object created from a RenderingSystem."""

    # pylint: disable=too-few-public-methods

    def __init__(
        self,
        game_object: GameObject,
        remove_from_system: Callable[["GraphicalObject"], None],
    ):
        self.__game_object = game_object
        self.__remove_from_system = remove_from_system

        self.__is_destroyed = False
        self.__remove_destroy_hook = game_object.on_destroy(self.destroy)

    def destroy(self):
        """Removes this object from the rendering system causing it to no longer
        be drawn.

        """

        if self.__is_destroyed:
            return

        self.__is_destroyed = True
        self.__remove_from_system(self)
        self.__remove_destroy_hook()


class Sprite(GraphicalObject):
    """A 2D image attached to a GameObject that moves and rotates
    according to a Transform.

    Create Sprites using RenderingSystem.new_sprite.
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

    Create Texts using RenderingSystem.new_text.
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


class RenderingSystem:
    """A collection of graphical objects."""

    def __init__(self):
        self._objects: set[_GraphicalObject] = set()

    def new_sprite(
        self,
        game_object: GameObject,
        surface: pygame.Surface,
        transform: Transform,
    ) -> Sprite:
        """Creates and returns a new sprite that will be drawn whenever
        this is rendered.

        """

        sprite = _Sprite(
            remove_from_system=self._discard,
            game_object=game_object,
            surface=surface,
            transform=transform,
        )
        self._objects.add(sprite)
        return sprite

    def new_text(
        self,
        game_object: GameObject,
        transform: Transform,
        font: pygame.font.Font,
        text: str,
    ):
        """Creates and returns a Text object that will be drawn whenever
        this is rendered.

        """

        text = _Text(
            remove_from_system=self._discard,
            game_object=game_object,
            transform=transform,
            text=text,
            font=font,
        )
        self._objects.add(text)
        return text

    def render(self, screen: pygame.Surface):
        """Renders all graphical objects in this system."""
        for obj in self._objects:
            obj.render(screen)

    def _discard(self, obj):
        self._objects.discard(obj)


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
