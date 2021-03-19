import math
import pygame

from game_object import GameObject
from transform import Transform


class Sprite:
    """A 2D image that moves and rotates according to a transform.

    Create Sprites using RenderingSystem.new_sprite."""
    def __init__(self, rendering_system, surface: pygame.Surface,
                 transform: Transform):
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
            self._surface,
            self._transform.angle() * 180 / math.pi)

        off_x = (self._surface.get_rect().centerx -
                 img_rotated.get_rect().centerx -
                 self._surface.get_rect().width / 2)
        off_y = (self._surface.get_rect().centery -
                 img_rotated.get_rect().centery -
                 self._surface.get_rect().height / 2)

        screen.blit(img_rotated, (x + off_x, y + off_y))


def add_sprite_component(go: GameObject, sprite: Sprite):
    def hook():
        sprite.disable()
    go.add_destroy_hook(hook)

    # TODO: Sprite component super jank, fix
    return lambda: go.remove_destroy_hook(hook)


class RenderingSystem:
    def __init__(self):
        self._sprites = set()

    def new_sprite(self, surface: pygame.Surface,
                   transform: Transform) -> Sprite:
        sprite = Sprite(self, surface, transform)
        self._sprites.add(sprite)
        return sprite

    def render(self, screen: pygame.Surface):
        for sprite in self._sprites:
            sprite.render(screen)
