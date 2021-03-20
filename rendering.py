import math
import pygame

from game_object import GameObject
from transform import Transform


class Sprite:
    """A 2D image that moves and rotates according to a transform.

    Create Sprites using RenderingSystem.new_sprite."""

    def __init__(
        self, rendering_system, surface: pygame.Surface, transform: Transform
    ):
        self._surface = surface
        self._transform = transform
        self._system = rendering_system

    def disable(self):
        """Temporarily removes this sprite from the rendering system.

        Use this to stop the sprite from getting drawn."""
        self._system._sprites.discard(self)

    def enable(self):
        """Adds the sprite back to the rendering system."""
        self._system._sprites.add(self)

    def render(self, screen: pygame.Surface):
        x = self._transform.x()
        y = self._transform.y()
        img_rotated = pygame.transform.rotate(
            self._surface, self._transform.angle() * 180 / math.pi
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


def add_sprite_component(go: GameObject, sprite: Sprite):
    def hook():
        sprite.disable()

    go.add_destroy_hook(hook)

    # TODO: Sprite component super jank, fix
    return lambda: go.remove_destroy_hook(hook)


class Text:
    def __init__(
        self,
        rendering_system: "RenderingSystem",
        text: str,
        font: pygame.font.Font,
    ):
        self._system = rendering_system
        self._font = font
        self._text = None
        self._rendered_text = None
        self._new_text = text
        self.x = 0
        self.y = 0
        self.color = pygame.Color(255, 255, 255)

    @property
    def text(self):
        if self._new_text is not None:
            return self._new_text
        return self._text

    @text.setter
    def text(self, new_value):
        if new_value != self._text:
            self._new_text = new_value

    def disable(self):
        self._system._sprites.discard(self)

    def enable(self):
        self._system._sprites.add(self)

    def render(self, screen: pygame.Surface):
        if self._new_text is not None:
            self._text = self._new_text
            self._rendered_text = self._font.render(
                self._text, False, self.color
            )
            self._new_text = None

        screen.blit(self._rendered_text, (self.x, self.y))


class RenderingSystem:
    def __init__(self):
        self._sprites = set()

    def new_sprite(
        self, surface: pygame.Surface, transform: Transform
    ) -> Sprite:
        sprite = Sprite(self, surface, transform)
        self._sprites.add(sprite)
        return sprite

    def new_text(self, font: pygame.font.Font, text: str):
        text = Text(self, text, font)
        self._sprites.add(text)
        return text

    def render(self, screen: pygame.Surface):
        for sprite in self._sprites:
            sprite.render(screen)
