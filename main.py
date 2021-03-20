import pygame
import random

from game_env import GameEnv
from game_object import GameObject
from game_object_coroutine import GameObjectCoroutine, resume_after
from hittable import Hittable
from physics import add_physics_component
from rendering import add_sprite_component
from spaceship import make_spaceship
from transform import Transform


def make_asteroid(
    game: GameEnv,
    *,
    x: float = 400,
    y: float = 300,
    vx: float = 0,
    vy: float = 0
) -> GameObject:
    go = game.game_objects.new_object()

    img = pygame.transform.scale(
        pygame.image.load("images/asteroid.png").convert_alpha(), (50, 50)
    )

    transform = Transform()
    sprite = game.graphics.new_sprite(img, transform)
    body = game.physics.new_circle_body(transform=transform, radius=25, mass=5)

    # Register the sprite and physics body as components so that they
    # get disabled when the object is destroyed
    add_physics_component(go, body)
    add_sprite_component(go, sprite)

    transform.set_local_x(x)
    transform.set_local_y(y)
    body.velocity_x = vx
    body.velocity_y = vy

    class AsteroidHittable(Hittable):
        def __init__(self):
            self._num_hits = 0

        def hit(self):
            print("Asteroid got hit!")
            self._num_hits += 1

            if self._num_hits >= 10:
                go.destroy()
                make_explosion(game, x=transform.x(), y=transform.y())

    body.add_data(AsteroidHittable())

    return go


def make_asteroid_generator(
    game: GameEnv,
    x: float,
    y: float,
    width: float,
    height: float,
    interval_ms: float,
) -> GameObject:
    go = game.game_objects.new_object()

    def generate_asteroids():
        while True:
            make_asteroid(
                game,
                x=random.uniform(x, x + width),
                y=random.uniform(y, y + height),
                vx=random.gauss(0, 0.03),
                vy=random.gauss(0, 0.03),
            )
            yield resume_after(time=game.time, delay_ms=interval_ms)

    GameObjectCoroutine(go, generate_asteroids()).start()

    return go


def make_explosion(game: GameEnv, x: float, y: float):
    go = game.game_objects.new_object()
    transform = Transform()
    transform.set_local_x(x)
    transform.set_local_y(y)

    def animation():
        for n in range(25):
            sprite = game.graphics.new_sprite(explosion_images[n], transform)
            remove_component = add_sprite_component(go, sprite)
            yield resume_after(game.time, delay_ms=20)
            remove_component()
            sprite.disable()
        go.destroy()

    GameObjectCoroutine(go, animation()).start()


if __name__ == "__main__":
    pygame.init()

    screen = pygame.display.set_mode((800, 600))

    global explosion_images
    explosion_images = [
        pygame.image.load("images/explosion_%d.png" % n).convert_alpha()
        for n in range(25)
    ]

    game = GameEnv()

    make_spaceship(game, x=400, y=200)
    make_asteroid_generator(
        game, x=0, y=0, width=800, height=600, interval_ms=3000
    )

    while True:
        delta_time = pygame.time.delay(20)
        game.inputs.start_new_frame()

        if game.inputs.did_quit():
            break

        game.game_objects.update(delta_time)
        game.time.run_callbacks()
        game.physics.update(delta_time)

        # Clear the screen
        screen.fill(pygame.Color(0, 0, 0))

        game.graphics.render(screen)
        pygame.display.update()
