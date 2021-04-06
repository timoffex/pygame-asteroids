import math
import pinject
import pygame
import pygame.gfxdraw

import game_objects
from game_objects import GameObject

import graphics
from graphics import Text

from ammo_display import AmmoDisplay
from asteroid import AsteroidGeneratorFactory
from game_time import GameTime
from heart_display import HeartDisplayFactory
from inputs import Inputs
from physics import PhysicsSystem
from player import Player
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

    def provide_bullet_images(self):
        print("Loading bullet images")
        return [pygame.image.load("images/bullet.png").convert_alpha()]

    def provide_extra_bullets_image(self):
        print("Loading bullet drop image")
        return pygame.image.load("images/bullet_drop.png").convert_alpha()

    def provide_asteroid_images(self):
        print("Loading asteroid images")
        return [pygame.image.load("images/asteroid.png").convert_alpha()]

    def provide_heart_image(self):
        print("Loading heart image")
        return pygame.image.load("images/heart.png").convert_alpha()

    def provide_extra_heart_image(self):
        print("Loading extra-heart image")
        return pygame.image.load("images/extra_heart.png").convert_alpha()


class Application:
    def __init__(
        self,
        inputs: Inputs,
        game_time: GameTime,
        physics_system: PhysicsSystem,
        asteroid_generator_factory: AsteroidGeneratorFactory,
        spaceship_factory: SpaceshipFactory,
        heart_display_factory: HeartDisplayFactory,
    ):
        self._inputs = inputs
        self._game_time = game_time
        self._physics_system = physics_system
        self._asteroid_generator_factory = asteroid_generator_factory
        self._spaceship_factory = spaceship_factory
        self._heart_display_factory = heart_display_factory

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

        body = self._physics_system.new_body(
            game_object=game_objects.new_object(),
            mass=math.inf,
            transform=t,
        )
        body.add_circle_collider(radius=radius)

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

        counter_transform = Transform()
        counter_transform.set_local_x(400)
        counter_transform.set_local_y(20)
        counter_text = graphics.new_text(
            game_object=game_objects.new_object(),
            transform=counter_transform,
            font=pygame.font.Font(None, 36),
            text="",
        )
        counter = AsteroidCounter(counter_text)

        fps_transform = Transform()
        fps_transform.set_local_x(700)
        fps_transform.set_local_y(30)
        fps_text = graphics.new_text(
            game_object=game_objects.new_object(),
            transform=fps_transform,
            font=pygame.font.Font(None, 36),
            text="",
        )
        fps_text.color = pygame.Color(200, 200, 0)

        player = Player()
        spaceship = self._spaceship_factory(x=400, y=200, player=player)

        def on_player_hearts_changed(new_value: int):
            if new_value <= 0:
                print("Player's hearts are <= 0")
                spaceship.destroy()

        player.on_hearts_changed(on_player_hearts_changed)

        heart_display_transform = Transform()
        heart_display_transform.set_local_x(20)
        heart_display_transform.set_local_y(20)
        heart_display_go = game_objects.new_object()
        self._heart_display_factory(
            heart_display_go, heart_display_transform, player
        )

        ammo_display_transform = Transform()
        ammo_display_transform.set_local_x(20)
        ammo_display_transform.set_local_y(50)
        AmmoDisplay(
            game_object=game_objects.new_object(),
            player=player,
            transform=ammo_display_transform,
        )

        self._asteroid_generator_factory(
            counter=counter,
            x=0,
            y=0,
            width=800,
            height=600,
            interval_ms=3000,
        )

        self.make_borders()

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

            game_objects.update(delta_time)
            self._game_time.run_callbacks()
            self._physics_system.update(delta_time)

            # Clear the screen
            screen.fill(pygame.Color(0, 0, 0))

            # Draw quadtree constructed in physics step
            # for box in self._physics_system.debug_get_bounding_boxes():
            #     pygame.gfxdraw.rectangle(
            #         screen,
            #         pygame.Rect(
            #             box.x_min,
            #             box.y_min,
            #             box.width,
            #             box.height,
            #         ),
            #         pygame.Color(255, 0, 255),
            #     )

            graphics.render(screen)
            pygame.display.update()


if __name__ == "__main__":
    app = pinject.new_object_graph(
        binding_specs=[ApplicationBindingSpec()]
    ).provide(Application)
    app.start()
