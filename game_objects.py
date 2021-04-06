"""This module defines GameObjects and keeps track of all GameObjects in the
game.

"""

from abc import ABC, abstractmethod
from typing import Callable

from hook_list import HookList, Unsubscriber


UpdateHook = Callable[[float], None]
"""A function that is attached to a GameObject and runs once on every frame
until that GameObject is destroyed.

The function's argument is the approximate number of milliseconds that have
passed since the last frame.
"""


DestroyHook = Callable[[], None]
"""A function that runs when a GameObject is destroyed."""


class GameObject(ABC):
    """An object in the game.

    Create GameObjects using ``new_object``.

    The purpose of GameObject is to be able to refer to a logical
    entity in the game. You can add update hooks to a GameObject that
    will run every frame as long as the GameObject is alive and will
    stop after it is destroyed. You can also add a hook to detect when
    the object is destroyed.

    A GameObject can have a parent GameObject, in which case it is
    destroyed if the parent is destroyed. This is useful for objects
    that are logically 'part' of another object, like the gun system
    on a spaceship.

    """

    @abstractmethod
    def on_update(self, hook: UpdateHook) -> Unsubscriber:
        """Adds a hook that runs on every frame until this GameObject is
        destroyed.

        """

    @abstractmethod
    def on_destroy(self, hook: DestroyHook) -> Unsubscriber:
        """Adds a hook that runs when this GameObject is destroyed."""

    @abstractmethod
    def destroy(self):
        """Destroys this GameObject causing any registered update hooks to stop
        running on every frame.

        """

    @abstractmethod
    def set_parent(self, parent: "GameObject"):
        """Sets the parent of this GameObject, causing it to be destroyed if
        the parent is destroyed.

        """


def new_object() -> GameObject:
    """Creates and returns a new GameObject."""
    game_object = _GameObject()
    _game_objects.add(game_object)
    return game_object


def update(delta_time: float):
    """Updates all GameObjects."""
    # Make a copy of _game_objects in case new objects are created or old
    # objects are destroyed during update
    game_objects = set(_game_objects)
    for obj in game_objects:
        obj.update(delta_time=delta_time)


class _GameObject(GameObject):
    def __init__(self):
        self._update_hooks = HookList()
        self._destroy_hooks = HookList()
        self._is_destroyed = False

        self._remove_parent_destroy_hook = None

    def on_update(self, hook: UpdateHook) -> Unsubscriber:
        return self._update_hooks.append(hook)

    def on_destroy(self, hook: DestroyHook) -> Unsubscriber:
        return self._destroy_hooks.append(hook)

    def destroy(self):
        if self._is_destroyed:
            return

        self._is_destroyed = True
        self._destroy_hooks.run_hooks()
        _discard_game_object(self)

    def update(self, delta_time: float):
        """Runs the update hooks on this GameObject."""
        self._update_hooks.run_hooks(delta_time=delta_time)

    def set_parent(self, parent: "GameObject"):
        """Sets the parent of this GameObject, causing it to be destroyed if
        the parent is destroyed.

        """
        if self._remove_parent_destroy_hook:
            self._remove_parent_destroy_hook()

        self._remove_parent_destroy_hook = (
            parent.on_destroy(self.destroy) if parent else None
        )


_game_objects: set[_GameObject] = set()


def _discard_game_object(game_object: _GameObject):
    """Removes the game_object."""
    _game_objects.discard(game_object)
