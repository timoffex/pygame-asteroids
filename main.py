import math
import pinject
import pygame
import pygame.gfxdraw

from asteroid import AsteroidGeneratorFactory
from game_object import GameObjectSystem
from game_time import GameTime
from inputs import Inputs
from physics import PhysicsSystem
from rendering import RenderingSystem, Text
from spaceship import SpaceshipFactory
from transform import Transform


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

    # The following should always be injected in provider form and
    # used lazily because the Pinject object graph is (intentionally)
    # constructed before pygame is initialized. For example, inject
    # "provide_explosion_images" and call it when you need explosion
    # images; don't inject "explosion_images" directly.

    def provide_explosion_images(self):
        print("Loading explosion images")
        return [
            pygame.image.load(f"images/explosion_{n}.png").convert_alpha()
            for n in range(25)
        ]

    def provide_asteroid_images(self):
        print("Loading asteroid images")
        return [pygame.image.load("images/asteroid.png").convert_alpha()]


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

    def add_border(
        self,
        border_x: float,
        border_y: float,
        outward_x: float,
        outward_y: float,
        radius: float,
    ):
        t = Transform()
        t.set_local_x(border_x + outward_x * radius)
        t.set_local_y(border_y + outward_y * radius)

        self._physics_system.new_circle_body(
            game_object=self._game_object_system.new_object(),
            mass=math.inf,
            transform=t,
            radius=radius,
        )

    def make_borders(self):
        """Creates the boundaries of the map by using very large invisible
        circles.

        """
        self.add_border(
            border_x=790, border_y=300, outward_x=1, outward_y=0, radius=5000
        )
        self.add_border(
            border_x=10, border_y=300, outward_x=-1, outward_y=0, radius=5000
        )
        self.add_border(
            border_x=400, border_y=10, outward_x=0, outward_y=-1, radius=5000
        )
        self.add_border(
            border_x=400, border_y=590, outward_x=0, outward_y=1, radius=5000
        )

    def start(self):
        pygame.init()

        screen = pygame.display.set_mode((800, 600))

        counter_text = self._rendering_system.new_text(
            pygame.font.Font(None, 36), ""
        )
        counter_text.x = 30
        counter_text.y = 30
        counter = AsteroidCounter(counter_text)

        fps_text = self._rendering_system.new_text(
            pygame.font.Font(None, 36), ""
        )
        fps_text.x = 700
        fps_text.y = 30
        fps_text.color = pygame.Color(200, 200, 0)

        self._spaceship_factory(x=400, y=200)
        self._asteroid_generator_factory(
            counter,
            x=0,
            y=0,
            width=800,
            height=600,
            interval_ms=3000,
        )

        self.make_borders()

        self._physics_system.debug_save_bounding_boxes = True

        last_ticks = pygame.time.get_ticks()
        while True:
            pygame.time.delay(20)

            new_ticks = pygame.time.get_ticks()
            delta_time = new_ticks - last_ticks
            fps_text.text = "fps: " + str(round(1000 / delta_time))
            last_ticks = new_ticks

            self._inputs.start_new_frame()

            if self._inputs.did_quit():
                break

            self._game_object_system.update(delta_time)
            self._game_time.run_callbacks()
            self._physics_system.update(delta_time)

            # Clear the screen
            screen.fill(pygame.Color(0, 0, 0))

            # Draw quadtree constructed in physics step
            for box in self._physics_system.debug_get_bounding_boxes():
                pygame.gfxdraw.rectangle(
                    screen,
                    pygame.Rect(
                        box.x_min,
                        box.y_min,
                        box.width,
                        box.height,
                    ),
                    pygame.Color(255, 0, 255),
                )

            self._rendering_system.render(screen)
            pygame.display.update()


if __name__ == "__main__":
    app = pinject.new_object_graph(
        binding_specs=[ApplicationBindingSpec()]
    ).provide(Application)
    app.start()
