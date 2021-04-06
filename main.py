import math


def main():
    import pygame
    import pygame.gfxdraw

    # Initialize pygame before loading any game modules
    pygame.init()
    screen = pygame.display.set_mode((800, 600))

    # Import game modules
    from ammo_display import AmmoDisplay
    from asteroid import make_asteroid_generator
    import game_time
    import game_objects
    import graphics
    from heart_display import HeartDisplay
    import inputs
    import physics
    from player import Player
    from spaceship import make_spaceship
    from transform import Transform

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
    spaceship = make_spaceship(x=400, y=200, player=player)

    def on_player_hearts_changed(new_value: int):
        if new_value <= 0:
            print("Player's hearts are <= 0")
            spaceship.destroy()

    player.on_hearts_changed(on_player_hearts_changed)

    heart_display_transform = Transform()
    heart_display_transform.set_local_x(20)
    heart_display_transform.set_local_y(20)
    heart_display_go = game_objects.new_object()
    HeartDisplay(player, heart_display_transform, heart_display_go)

    ammo_display_transform = Transform()
    ammo_display_transform.set_local_x(20)
    ammo_display_transform.set_local_y(50)
    AmmoDisplay(
        game_object=game_objects.new_object(),
        player=player,
        transform=ammo_display_transform,
    )

    make_asteroid_generator(
        x=0, y=0, width=800, height=600, interval_ms=3000, initial_asteroids=10
    )

    _make_borders()

    last_ticks = pygame.time.get_ticks()
    while True:
        pygame.time.delay(20)

        new_ticks = pygame.time.get_ticks()
        delta_time = new_ticks - last_ticks
        fps_text.text = "fps: " + str(round(1000 / delta_time))
        last_ticks = new_ticks

        inputs.start_new_frame()

        if inputs.did_quit():
            break

        game_objects.update(delta_time)
        game_time.run_callbacks()
        physics.update(delta_time)

        # Clear the screen
        screen.fill(pygame.Color(0, 0, 0))

        graphics.render(screen)
        pygame.display.update()


def _add_border(
    border_x: float,
    border_y: float,
    outward_x: float,
    outward_y: float,
    radius: float,
):
    import game_objects
    import physics
    from transform import Transform

    t = Transform()
    t.set_local_x(border_x + outward_x * radius)
    t.set_local_y(border_y + outward_y * radius)

    body = physics.new_body(
        game_object=game_objects.new_object(),
        mass=math.inf,
        transform=t,
    )
    body.add_circle_collider(radius=radius)


def _make_borders():
    """Creates the boundaries of the map by using very large invisible
    circles.

    """
    _add_border(
        border_x=790, border_y=300, outward_x=1, outward_y=0, radius=5000
    )
    _add_border(
        border_x=10, border_y=300, outward_x=-1, outward_y=0, radius=5000
    )
    _add_border(
        border_x=400, border_y=10, outward_x=0, outward_y=-1, radius=5000
    )
    _add_border(
        border_x=400, border_y=590, outward_x=0, outward_y=1, radius=5000
    )


if __name__ == "__main__":
    main()
