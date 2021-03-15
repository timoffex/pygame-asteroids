import math
import pygame
import pygame.gfxdraw

from physics import PhysicsSystem
from rendering import RenderingSystem
from transform import Transform


class Inputs:
    def __init__(self):
        self._did_quit = False

    def did_quit(self):
        return self._did_quit

    def is_key_down(self, key_code):
        return pygame.key.get_pressed()[key_code]

    def start_new_frame(self):
        for event in pygame.event.get():
            if event.type is pygame.QUIT:
                self._did_quit = True


class Spaceship:
    def __init__(self, physics: PhysicsSystem, graphics: RenderingSystem):
        img = pygame.transform.rotate(
            pygame.transform.scale(
                pygame.image.load("images/spaceship.png").convert_alpha(),
                (50, 50)),
            -90)

        self._transform = Transform()
        self._sprite = graphics.new_sprite(img, self._transform)
        self._body = physics.new_circle_body(
            transform=self._transform,
            radius=25,
            mass=1)

    def update(self, inputs: Inputs, delta_time: float):
        if inputs.is_key_down(pygame.K_d):
            self._transform.rotate(-delta_time / 100)
        if inputs.is_key_down(pygame.K_a):
            self._transform.rotate(delta_time / 100)

        if inputs.is_key_down(pygame.K_s):
            # Slow down gradually
            self._body.velocity_x *= math.pow(0.8, delta_time / 50)
            self._body.velocity_y *= math.pow(0.8, delta_time / 50)

        if inputs.is_key_down(pygame.K_w):
            # Speed up in the direction the ship is facing

            s = math.sin(self._transform.angle())
            c = math.cos(self._transform.angle())
            self._body.velocity_x += delta_time * c / 1000
            self._body.velocity_y -= delta_time * s / 1000


class Asteroid:
    def __init__(self, physics: PhysicsSystem, graphics: RenderingSystem,
                 *, x: float = 400, y: float = 300,
                 vx: float = 0, vy: float = 0):
        img = pygame.transform.scale(
            pygame.image.load("images/asteroid.png").convert_alpha(),
            (50, 50))

        self._transform = Transform()
        self._sprite = graphics.new_sprite(img, self._transform)
        self._body = physics.new_circle_body(
            transform=self._transform,
            radius=25,
            mass=5)

        self._transform.set_local_x(x)
        self._transform.set_local_y(y)
        self._body.velocity_x = vx
        self._body.velocity_y = vy


if __name__ == "__main__":
    pygame.init()

    screen = pygame.display.set_mode((800, 600))

    physics = PhysicsSystem()
    graphics = RenderingSystem()
    inputs = Inputs()

    spaceship = Spaceship(physics, graphics)
    asteroid1 = Asteroid(physics, graphics, x=300, y=300, vx=0.01, vy=0.01)
    asteroid2 = Asteroid(physics, graphics, x=500, y=300, vx=-0.01, vy=0.01)

    while True:
        delta_time = pygame.time.delay(20)
        inputs.start_new_frame()

        if inputs.did_quit():
            break

        spaceship.update(inputs, delta_time)
        physics.update(delta_time)

        # Clear the screen
        screen.fill(pygame.Color(0, 0, 0))

        graphics.render(screen)
        pygame.display.update()
