from typing import Protocol


class UpdateHook(Protocol):
    """Protocol for GameObject update hooks."""
    def __call__(self, update_hook: float) -> None: ...

class DestroyHook(Protocol):
    """Protocol for GameObject destroy hooks."""
    def __call__(self) -> None: ...


class GameObject:
    """An object in the game.

    Create GameObjects using GameObjectSystem.new_object.

    The purpose of GameObject is to be able to refer to a logical
    entity in the game. You can add update hooks to a GameObject that
    will run every frame as long as the GameObject is alive and will
    stop after it is destroyed. You can also add a hook to detect when
    the object is destroyed.

    """

    def __init__(self, game_object_system):
        self._system = game_object_system
        self._update_hooks = []
        self._destroy_hooks = []

    def add_update_hook(self, hook: UpdateHook):
        self._update_hooks.append(hook)

    def add_destroy_hook(self, hook: DestroyHook):
        self._destroy_hooks.append(hook)

    def update(self, delta_time: float):
        for hook in self._update_hooks:
            hook(delta_time)

    def destroy(self):
        self._system._game_objects.remove(self)

        for hook in self._destroy_hooks:
            hook()


class GameObjectSystem:
    def __init__(self):
        self._game_objects = set()

    def new_object(self) -> GameObject:
        go = GameObject(self)
        self._game_objects.add(go)
        return go

    def update(self, delta_time: float):
        for obj in self._game_objects:
            obj.update(delta_time=delta_time)
