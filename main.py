import math
import pygame
import random

from game_env import GameEnv
from game_object import GameObject
from game_object_coroutine import GameObjectCoroutine, resume_after
from physics import PhysicsBody, Collision, add_physics_component
from rendering import add_sprite_component
from transform import Transform


class Hittable:
    """Base class for objects that can be hit by a weapon."""

    def hit(self):
        ...


def make_bullet(
    game: GameEnv,
    *,
    x: float,
    y: float,
    angle: float,
    vx: float = 0,
    vy: float = 0,
    lifetime_ms: float = 10000
) -> GameObject:
    go = game.game_objects.new_object()

    img = pygame.transform.scale(
        pygame.image.load("images/asteroid.png").convert_alpha(), (5, 5)
    )

    transform = Transform()
    transform.set_local_x(x)
    transform.set_local_y(y)
    transform.set_local_angle(angle)

    add_sprite_component(go, game.graphics.new_sprite(img, transform))

    body = game.physics.new_circle_body(
        transform=transform, radius=2.5, mass=0.1
    )
    add_physics_component(go, body)

    speed = 0.1
    body.velocity_x = vx + speed * math.cos(angle)
    body.velocity_y = vy - speed * math.sin(angle)

    def on_collision(collision: Collision):
        hittable: Hittable
        hittable = next(
            (
                x
                for x in collision.body_other.get_data()
                if isinstance(x, Hittable)
            ),
            None,
        )

        if hittable:
            print("Bullet hit something hittable!", go)
            hittable.hit()
            go.destroy()

    body.add_collision_hook(on_collision)

    def destroy_after_lifetime():
        yield resume_after(game.time, delay_ms=lifetime_ms)
        go.destroy()

    GameObjectCoroutine(go, destroy_after_lifetime()).start()

    return go


class Guns:
    def __init__(
        self,
        game: GameEnv,
        *,
        shooting_transform: Transform,
        shooting_body: PhysicsBody,
        firing_delay_ms: float
    ):
        self._game = game
        self._shooting_transform = shooting_transform
        self._shooting_body = shooting_body
        self._last_shot_time = -math.inf
        self._firing_delay_ms = firing_delay_ms

    def is_ready_to_fire(self):
        return (
            pygame.time.get_ticks()
            > self._last_shot_time + self._firing_delay_ms
        )

    def fire(self):
        self._last_shot_time = pygame.time.get_ticks()
        make_bullet(
            self._game,
            x=self._shooting_transform.x(),
            y=self._shooting_transform.y(),
            angle=self._shooting_transform.angle(),
            vx=self._shooting_body.velocity_x,
            vy=self._shooting_body.velocity_y,
        )


def make_spaceship(game: GameEnv, x: float = 0, y: float = 0) -> GameObject:
    go = game.game_objects.new_object()

    img = pygame.transform.rotate(
        pygame.transform.scale(
            pygame.image.load("images/spaceship.png").convert_alpha(), (50, 50)
        ),
        -90,
    )

    transform = Transform()
    transform.set_local_x(x)
    transform.set_local_y(y)
    sprite = game.graphics.new_sprite(img, transform)
    body = game.physics.new_circle_body(transform=transform, radius=25, mass=1)

    # Register the sprite and physics body as components so that they
    # get disabled when the object is destroyed
    add_physics_component(go, body)
    add_sprite_component(go, sprite)

    guns = Guns(
        game,
        shooting_transform=transform,
        shooting_body=body,
        firing_delay_ms=50,
    )

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

        if game.inputs.is_key_down(pygame.K_SPACE) and guns.is_ready_to_fire():
            guns.fire()

    go.add_update_hook(update)
    return go


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
