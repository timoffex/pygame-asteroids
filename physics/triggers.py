from abc import abstractmethod
from dataclasses import dataclass
from game_object import GameObject
from transform import Transform
from typing import Callable, Protocol

from .collider import Collider


@dataclass(frozen=True)
class TriggerEvent:
    """The data for any kind of trigger zone event, including when something
    enters, exits or stays in the trigger zone.

    """

    trigger_zone: "TriggerCollider"
    other_collider: Collider


class TriggerHook(Protocol):
    """Protocol for trigger event handlers."""

    def __call__(self, trigger_event: TriggerEvent):
        ...


class TriggerCollider(Collider):
    """A zone that detects when it overlaps with other colliders.

    This is an abstract class. Create trigger zones of the desired shape
    by using methods on a PhysicsSystem object.

    """

    @abstractmethod
    def __init__(self, transform: Transform, game_object: GameObject):
        super().__init__()

        self._stay_hooks: list[TriggerHook] = []
        self._enter_hooks: list[TriggerHook] = []
        self._exit_hooks: list[TriggerHook] = []

        self._transform = transform
        self._is_destroyed = False
        self._game_object = game_object
        self._game_object.add_destroy_hook(self.destroy)

    @property
    def transform(self):
        return self._transform

    def destroy(self):
        if not self._is_destroyed:
            self._game_object.remove_destroy_hook(self.destroy)
            self._is_destroyed = True
        super().destroy()

    def on_trigger_stay(self, hook: TriggerHook) -> Callable[[], None]:
        """Adds a hook that runs on every frame that something is inside
        this collider.

        This returns a function that can be called to remove the added hook.

        """
        return self.__make_hook(self._stay_hooks, hook)

    def on_trigger_enter(self, hook: TriggerHook) -> Callable[[], None]:
        """Adds a hook that runs on the frame that something enters this
        collider.

        This returns a function that can be called to remove the added hook.

        """
        return self.__make_hook(self._enter_hooks, hook)

    def on_trigger_exit(self, hook: TriggerHook) -> Callable[[], None]:
        """Adds a hook that runs on the frame that something exits this
        collider.

        This returns a function that can be called to remove the added hook.

        """
        return self.__make_hook(self._exit_hooks, hook)

    def __make_hook(
        self, hook_list: list[TriggerHook], hook: TriggerHook
    ) -> Callable[[], None]:
        hook_list.append(hook)
        did_remove = False

        def remove_hook():
            nonlocal did_remove
            if not did_remove:
                hook_list.remove(hook)
                did_remove = True

        return remove_hook
