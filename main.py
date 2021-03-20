import pinject
import pygame
import random

from game_object import GameObject, GameObjectSystem
from game_object_coroutine import GameObjectCoroutine, resume_after
from game_time import GameTime
from hittable import Hittable
from inputs import Inputs
from physics import PhysicsSystem, add_physics_component
from rendering import RenderingSystem, Text, add_sprite_component
from spaceship import SpaceshipFactory
from transform import Transform


class Counter:
    def __init__(self, text: Text, count: int):
        self._count = 0
        self._text = text
        self._text.text = str(self._count)

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, new_value):
        self._count = new_value
        self._text.text = str(self._count)


class AsteroidFactory:
    @pinject.copy_args_to_internal_fields
    def __init__(
        self,
        game_object_system,
        physics_system,
        rendering_system,
        explosion_factory,
    ):
        pass

    def __call__(
        self,
        counter: Counter,
        *,
        x: float = 400,
        y: float = 300,
        vx: float = 0,
        vy: float = 0
    ) -> GameObject:
        go = self._game_object_system.new_object()

        img = pygame.transform.scale(
            pygame.image.load("images/asteroid.png").convert_alpha(), (50, 50)
        )

        transform = Transform()
        sprite = self._rendering_system.new_sprite(img, transform)
        body = self._physics_system.new_circle_body(
            transform=transform, radius=25, mass=5
        )

        # Register the sprite and physics body as components so that they
        # get disabled when the object is destroyed
        add_physics_component(go, body)
        add_sprite_component(go, sprite)

        transform.set_local_x(x)
        transform.set_local_y(y)
        body.velocity_x = vx
        body.velocity_y = vy

        class AsteroidHittable(Hittable):
            def __init__(self, explosion_factory):
                self._num_hits = 0
                self._explosion_factory = explosion_factory

            def hit(self):
                print("Asteroid got hit!")
                self._num_hits += 1

                if self._num_hits >= 10:
                    go.destroy()
                    self._explosion_factory(x=transform.x(), y=transform.y())
                    counter.count += 1

        body.add_data(AsteroidHittable(self._explosion_factory))

        return go


class AsteroidGeneratorFactory:
    def __init__(
        self,
        game_object_system: GameObjectSystem,
        game_time: GameTime,
        asteroid_factory: AsteroidFactory,
    ):
        self._game_objects = game_object_system
        self._time = game_time
        self._asteroid_factory = asteroid_factory

    def __call__(
        self,
        counter: Counter,
        x: float,
        y: float,
        width: float,
        height: float,
        interval_ms: float,
    ) -> GameObject:
        go = self._game_objects.new_object()

        def generate_asteroids():
            while True:
                self._asteroid_factory(
                    counter,
                    x=random.uniform(x, x + width),
                    y=random.uniform(y, y + height),
                    vx=random.gauss(0, 0.03),
                    vy=random.gauss(0, 0.03),
                )
                yield resume_after(time=self._time, delay_ms=interval_ms)

        GameObjectCoroutine(go, generate_asteroids()).start()

        return go


class ExplosionFactory:
    @pinject.copy_args_to_internal_fields
    def __init__(self, game_object_system, rendering_system, game_time):
        self._game_object_system: GameObjectSystem
        self._rendering_system: RenderingSystem
        self._game_time: GameTime
        pass

    def __call__(self, x: float, y: float):
        go = self._game_object_system.new_object()
        transform = Transform()
        transform.set_local_x(x)
        transform.set_local_y(y)

        def animation():
            for n in range(25):
                sprite = self._rendering_system.new_sprite(
                    explosion_images[n], transform
                )
                remove_component = add_sprite_component(go, sprite)
                yield resume_after(self._game_time, delay_ms=20)
                remove_component()
                sprite.disable()
            go.destroy()

        GameObjectCoroutine(go, animation()).start()


class Application:
    def __init__(
        self,
        inputs: Inputs,
        game_time: GameTime,
        game_object_system: GameObjectSystem,
        rendering_system: RenderingSystem,
        physics_system: PhysicsSystem,
        asteroid_generator_factory: AsteroidGeneratorFactory,
        spaceship_factory: SpaceshipFactory,
    ):
        self._inputs = inputs
        self._game_time = game_time
        self._game_object_system = game_object_system
        self._physics_system = physics_system
        self._rendering_system = rendering_system
        self._asteroid_generator_factory = asteroid_generator_factory
        self._spaceship_factory = spaceship_factory
        pass

    def start(self):
        pygame.init()

        screen = pygame.display.set_mode((800, 600))

        global explosion_images
        explosion_images = [
            pygame.image.load("images/explosion_%d.png" % n).convert_alpha()
            for n in range(25)
        ]

        counter_text = self._rendering_system.new_text(
            pygame.font.Font(None, 36), ""
        )
        counter_text.x = 30
        counter_text.y = 30
        counter = Counter(counter_text, count=30)

        self._spaceship_factory(x=400, y=200)
        self._asteroid_generator_factory(
            counter,
            x=0,
            y=0,
            width=800,
            height=600,
            interval_ms=3000,
        )

        while True:
            delta_time = pygame.time.delay(20)
            self._inputs.start_new_frame()

            if self._inputs.did_quit():
                break

            self._game_object_system.update(delta_time)
            self._game_time.run_callbacks()
            self._physics_system.update(delta_time)

            # Clear the screen
            screen.fill(pygame.Color(0, 0, 0))

            self._rendering_system.render(screen)
            pygame.display.update()


if __name__ == "__main__":
    app = pinject.new_object_graph().provide(Application)
    app.start()
