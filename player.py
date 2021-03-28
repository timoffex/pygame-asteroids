from typing import Callable, Protocol


class Unsubscriber(Protocol):
    def __call__(self):
        ...


class Player:
    def __init__(self):
        self._hearts = 3
        self._hearts_listeners: list[Callable[[int], None]] = []

        self.bullets = 100

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
