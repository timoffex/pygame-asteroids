from abc import ABC, abstractmethod
from game_object import GameObjectSystem
from physics import PhysicsSystem, TriggerEvent
from rendering import RenderingSystem
from transform import Transform
from utils import first_where


class ExtraBulletCollector(ABC):
    """Abstract base class for colliders that can collect bullet drops.

    If a collider has an ExtraBulletCollector in its data, it will
    collect a bullet drop upon touching it.

    """

    @abstractmethod
    def gain_bullets(self, amount: int):
        pass


class ExtraBulletFactory:
    def __init__(
        self,
        game_object_system: GameObjectSystem,
        physics_system: PhysicsSystem,
        rendering_system: RenderingSystem,
        provide_extra_bullets_image,
    ):
        self._game_object_system = game_object_system
        self._physics_system = physics_system
        self._rendering_system = rendering_system
        self._provide_extra_bullets_image = provide_extra_bullets_image

    def __call__(self, x: float, y: float, amount: int):
        """Spawns a bullet container at (x, y) with the given number of
        bullets.

        """

        go = self._game_object_system.new_object()
        transform = Transform()
        transform.set_local_x(x)
        transform.set_local_y(y)

        self._rendering_system.new_sprite(
            game_object=go,
            surface=self._provide_extra_bullets_image(),
            transform=transform,
        )

        trigger_zone = self._physics_system.new_circle_trigger(
            radius=16, game_object=go, transform=transform
        )

        is_collected = False

        def handle_trigger_enter(trigger_event: TriggerEvent):
            nonlocal is_collected

            if is_collected:
                return

            bullet_collector = first_where(
                lambda x: isinstance(x, ExtraBulletCollector),
                trigger_event.other_collider.get_data(),
            )

            if bullet_collector:
                is_collected = True
                bullet_collector.gain_bullets(amount=amount)
                go.destroy()

        trigger_zone.on_trigger_enter(handle_trigger_enter)
