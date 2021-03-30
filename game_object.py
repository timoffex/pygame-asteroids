from hook_list import HookList
from typing import Protocol


class UpdateHook(Protocol):
    """Protocol for GameObject update hooks."""

    def __call__(self, update_hook: float) -> None:
        ...


class DestroyHook(Protocol):
    """Protocol for GameObject destroy hooks."""

    def __call__(self) -> None:
        ...


class GameObject:
    """An object in the game.

    Create GameObjects using GameObjectSystem.new_object.

    The purpose of GameObject is to be able to refer to a logical
    entity in the game. You can add update hooks to a GameObject that
    will run every frame as long as the GameObject is alive and will
    stop after it is destroyed. You can also add a hook to detect when
    the object is destroyed.

    A GameObject can have a parent GameObject, in which case it is
    destroyed if the parent is destroyed. This is useful for objects
    that are logically "part" of another object, like the gun system
    on a spaceship.

    """

    def __init__(self, game_object_system):
        self._system = game_object_system
        self._update_hooks = HookList()
        self._destroy_hooks = HookList()
        self._is_destroyed = False

        self._remove_parent_destroy_hook = None

    def on_update(self, hook: UpdateHook):
        return self._update_hooks.append(hook)

    def on_destroy(self, hook: DestroyHook):
        return self._destroy_hooks.append(hook)

    def update(self, delta_time: float):
        self._update_hooks.run_hooks(delta_time=delta_time)

    def destroy(self):
        if self._is_destroyed:
            return

        self._system._game_objects.discard(self)

        self._destroy_hooks.run_hooks()

    def set_parent(self, parent: "GameObject"):
        """Sets the parent of this GameObject, causing it to be destroyed if
        the parent is destroyed.

        """
        if self._remove_parent_destroy_hook:
            self._remove_parent_destroy_hook()

        self._remove_parent_destroy_hook = (
            parent.on_destroy(self.destroy) if parent else None
        )


class GameObjectSystem:
    def __init__(self):
        self._game_objects = set()

    def new_object(self) -> GameObject:
        go = GameObject(self)
        self._game_objects.add(go)
        return go

    def update(self, delta_time: float):
        # Make a copy of self._game_objects in case new objects are
        # created or old objects are destroyed during update
        game_objects = set(self._game_objects)
        for obj in game_objects:
            obj.update(delta_time=delta_time)
