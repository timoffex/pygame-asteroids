import math
import pygame
import pygame.gfxdraw

from game_object import GameObject, GameObjectSystem
from physics import PhysicsSystem, add_physics_component
from rendering import RenderingSystem, add_sprite_component
from transform import Transform


class Inputs:
    """Class that keeps track of all user input information on every frame.

    This class is responsible for calling `pygame.event.get()` and no
    other code should touch the pygame.event or the pygame.key
    functions.

    """

    def __init__(self):
        self._did_quit = False

    def did_quit(self):
        """Returns whether the application received the QUIT signal."""
        return self._did_quit

    def is_key_down(self, key_code):
        """Returns whether the specified key is currently pressed.

        The key_code should be one of the `pygame.K_` constants, such as
        pygame.K_a (the A key) or pygame.K_SPACE (the space bar).

        """
        return pygame.key.get_pressed()[key_code]

    def start_new_frame(self):
        """Processes events at the start of a new frame.

        Call this before doing any extra processing for the frame.

        """
        for event in pygame.event.get():
            if event.type is pygame.QUIT:
                self._did_quit = True


class GameSystems:
    """A container object to keep track of all game systems."""

    def __init__(self):
        self.physics = PhysicsSystem()
        self.graphics = RenderingSystem()
        self.inputs = Inputs()
        self.game_objects = GameObjectSystem()


def make_spaceship(game: GameSystems) -> GameObject:
    go = game.game_objects.new_object()

    img = pygame.transform.rotate(
        pygame.transform.scale(
            pygame.image.load("images/spaceship.png").convert_alpha(),
            (50, 50)),
        -90)

    transform = Transform()
    sprite = game.graphics.new_sprite(img, transform)
    body = game.physics.new_circle_body(
        transform=transform,
        radius=25,
        mass=1)

    # Register the sprite and physics body as components so that they
    # get disabled when the object is destroyed
    add_physics_component(go, body)
    add_sprite_component(go, sprite)

    def update(delta_time: float) -> None:
        if game.inputs.is_key_down(pygame.K_d):
            transform.rotate(-delta_time / 100)
        if game.inputs.is_key_down(pygame.K_a):
            transform.rotate(delta_time / 100)

        if game.inputs.is_key_down(pygame.K_s):
            # Slow down gradually
            body.velocity_x *= math.pow(0.8, delta_time / 50)
            body.velocity_y *= math.pow(0.8, delta_time / 50)

        if game.inputs.is_key_down(pygame.K_w):
            # Speed up in the direction the ship is facing

            s = math.sin(transform.angle())
            c = math.cos(transform.angle())
            body.velocity_x += delta_time * c / 1000
            body.velocity_y -= delta_time * s / 1000

    go.add_update_hook(update)
    return go


def make_asteroid(game: GameSystems, *,
                  x: float = 400,
                  y: float = 300,
                  vx: float = 0,
                  vy: float = 0) -> GameObject:
    go = game.game_objects.new_object()

    img = pygame.transform.scale(
        pygame.image.load("images/asteroid.png").convert_alpha(),
        (50, 50))

    transform = Transform()
    sprite = game.graphics.new_sprite(img, transform)
    body = game.physics.new_circle_body(
        transform=transform,
        radius=25,
        mass=5)

    # Register the sprite and physics body as components so that they
    # get disabled when the object is destroyed
    add_physics_component(go, body)
    add_sprite_component(go, sprite)

    transform.set_local_x(x)
    transform.set_local_y(y)
    body.velocity_x = vx
    body.velocity_y = vy

    return go


if __name__ == "__main__":
    pygame.init()

    screen = pygame.display.set_mode((800, 600))

    game = GameSystems()

    make_spaceship(game)
    make_asteroid(game, x=300, y=300, vx=0.01, vy=0.01)
    make_asteroid(game, x=500, y=300, vx=-0.01, vy=0.01)

    while True:
        delta_time = pygame.time.delay(20)
        game.inputs.start_new_frame()

        if game.inputs.did_quit():
            break

        game.game_objects.update(delta_time)
        game.physics.update(delta_time)

        # Clear the screen
        screen.fill(pygame.Color(0, 0, 0))

        game.graphics.render(screen)
        pygame.display.update()
