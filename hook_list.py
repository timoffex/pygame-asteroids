"""Defines the HookList class that manages a list of hooks."""

from typing import Protocol


class HookList:
    """A list of functions.

    You can add to the list using append() which returns a function
    that can be called to remove the function from the list.

    The run_hooks() method runs all registered functions with the
    specified arguments.

    """

    def __init__(self):
        self.__listeners = []

    def append(self, hook) -> "Unsubscriber":
        """Add a hook to the list.

        This returns a function that can be called to remove the hook.
        It is safe to call the function multiple times: calls after the
        first one do nothing.

        """

        self.__listeners.append(hook)

        did_unsubscribe = False

        def unsubscribe():
            nonlocal did_unsubscribe
            if did_unsubscribe:
                return

            did_unsubscribe = True
            self.__listeners.remove(hook)

        return unsubscribe

    def run_hooks(self, *args, **kwargs):
        """Runs all hooks in the list.

        Any changes to the list of hooks during this operation only take
        effect after the method finishes.

        """

        listeners = list(self.__listeners)
        for listener in listeners:
            listener(*args, **kwargs)


# pylint: disable=too-few-public-methods
class Unsubscriber(Protocol):
    """A function that can be called to unsubscribe from a HookList.

    It is safe to call this function multiple times: calls after the
    first one are no-ops.

    """

    def __call__(self):
        ...
