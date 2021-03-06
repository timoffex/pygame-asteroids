from typing import Callable, Protocol


class Unsubscriber(Protocol):
    def __call__(self):
        ...


class Player:
    def __init__(self):
        self._hearts = 3
        self._hearts_listeners: list[Callable[[int], None]] = []

        self._bullets = 100
        self._bullets_listeners: list[Callable[int], None] = []

    @property
    def bullets(self):
        return self._bullets

    @bullets.setter
    def bullets(self, new_value):
        self._bullets = new_value
        listeners = self._bullets_listeners
        for listener in listeners:
            listener(new_value)

    def on_bullets_changed(
        self, listener: Callable[[int], None]
    ) -> Unsubscriber:
        self._bullets_listeners.append(listener)
        did_unsubscribe = False

        def unsubscribe():
            nonlocal did_unsubscribe
            did_unsubscribe = True
            self._bullets_listeners.remove(listener)

        return unsubscribe

    @property
    def hearts(self):
        return self._hearts

    def decrement_hearts(self):
        self._change_hearts(self.hearts - 1)

    def increment_hearts(self):
        self._change_hearts(self.hearts + 1)

    def _change_hearts(self, new_value):
        self._hearts = new_value
        listeners = list(self._hearts_listeners)
        for listener in listeners:
            listener(self._hearts)

    def on_hearts_changed(
        self, listener: Callable[[int], None]
    ) -> Unsubscriber:
        self._hearts_listeners.append(listener)
        did_unsubscribe = False

        def unsubscribe():
            nonlocal did_unsubscribe
            if not did_unsubscribe:
                did_unsubscribe = True
                self._hearts_listeners.remove(listener)

        return unsubscribe
