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

    A GameObject can have a parent GameObject, in which case it is
    destroyed if the parent is destroyed. This is useful for objects
    that are logically "part" of another object, like the gun system
    on a spaceship.

    """

    def __init__(self, game_object_system):
        self._system = game_object_system
        self._update_hooks = []
        self._destroy_hooks = []
        self._is_destroyed = False

        self._parent = None

    def add_update_hook(self, hook: UpdateHook):
        self._update_hooks.append(hook)

    def add_destroy_hook(self, hook: DestroyHook):
        self._destroy_hooks.append(hook)

    def remove_destroy_hook(self, hook):
        self._destroy_hooks.remove(hook)

    def update(self, delta_time: float):
        hooks = list(self._update_hooks)
        for hook in hooks:
            hook(delta_time)

    def destroy(self):
        if self._is_destroyed:
            return

        self._system._game_objects.discard(self)

        hooks = list(self._destroy_hooks)
        for hook in hooks:
            hook()

    def set_parent(self, parent: 'GameObject'):
        """Sets the parent of this GameObject, causing it to be destroyed if
        the parent is destroyed.

        """
        if self._parent:
            self._parent.remove_destroy_hook(self.destroy)

        self._parent = parent
        if self._parent:
            self._parent.add_destroy_hook(self.destroy)


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
