import pinject
import pygame

from asteroid import AsteroidGeneratorFactory
from game_object import GameObjectSystem
from game_time import GameTime
from inputs import Inputs
from physics import PhysicsSystem
from rendering import RenderingSystem, Text
from spaceship import SpaceshipFactory


class AsteroidCounter:
    """A graphical counter that keeps track of the number of asteroids
    that got destroyed.

    """

    def __init__(self, text: Text):
        self._count = 0
        self._text = text
        self._text.text = str(self._count)

    def increment(self):
        self._count += 1
        self._text.text = str(self._count)


class ApplicationBindingSpec(pinject.BindingSpec):
    def provide_explosion_images(self):
        # This should always be injected as a provider and used
        # lazily, since the Pinject object graph is constructed before
        # pygame is initialized! So inject "provide_explosion_images"
        # and call it when you need explosion images; don't inject
        # "explosion_images" directly.
        print("Loading explosion images")
        return [
            pygame.image.load("images/explosion_%d.png" % n).convert_alpha()
            for n in range(25)
        ]


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

        counter_text = self._rendering_system.new_text(
            pygame.font.Font(None, 36), ""
        )
        counter_text.x = 30
        counter_text.y = 30
        counter = AsteroidCounter(counter_text)

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
    app = pinject.new_object_graph(
        binding_specs=[ApplicationBindingSpec()]
    ).provide(Application)
    app.start()
