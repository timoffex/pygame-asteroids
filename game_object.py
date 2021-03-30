"""Defines the concept of a GameObject."""

from abc import ABC, abstractmethod
from typing import Callable, Protocol

from hook_list import HookList, Unsubscriber


class UpdateHook(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol for GameObject update hooks."""

    def __call__(self, update_hook: float) -> None:
        ...


class DestroyHook(Protocol):  # pylint: disable=too-few-public-methods
    """Protocol for GameObject destroy hooks."""

    def __call__(self) -> None:
        ...


class GameObject(ABC):
    """An object in the game.

    Create GameObjects using GameObjectSystem.new_object.

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


class GameObjectSystem:
    """A collection of GameObjects."""

    def __init__(self):
        self._game_objects: set[_GameObject] = set()

    def new_object(self) -> GameObject:
        """Creates and returns a new GameObject inside this system."""
        game_object = _GameObject(self._discard_game_object)
        self._game_objects.add(game_object)
        return game_object

    def update(self, delta_time: float):
        """Updates all GameObjects in this system."""
        # Make a copy of self._game_objects in case new objects are
        # created or old objects are destroyed during update
        game_objects = set(self._game_objects)
        for obj in game_objects:
            obj.update(delta_time=delta_time)

    def _discard_game_object(self, game_object: "_GameObject"):
        """Removes the game_object from this system."""
        self._game_objects.discard(game_object)


class _GameObject(GameObject):
    def __init__(self, discard_self: Callable[["_GameObject"], None]):
        self._discard_self = discard_self
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
        self._discard_self(self)
        self._destroy_hooks.run_hooks()

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
