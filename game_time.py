"""This module allows scheduling callbacks to run in the game's update loop."""

from typing import Callable

import heapq
import pygame


_sorted_scheduled_events: list["_ScheduledEvent"] = []


def run_after_delay(delay_ms: float, callback: Callable[[], None]):
    """Schedules a callback to run after the specified delay."""
    heapq.heappush(
        _sorted_scheduled_events,
        _ScheduledEvent(
            time=pygame.time.get_ticks() + delay_ms, callback=callback
        ),
    )


def run_callbacks():
    """Runs all callbacks whose time has come."""
    while len(_sorted_scheduled_events) > 0:
        event = heapq.heappop(_sorted_scheduled_events)
        if pygame.time.get_ticks() >= event.time:
            event.callback()
        else:
            # Add the event back
            heapq.heappush(_sorted_scheduled_events, event)
            break


class _ScheduledEvent:  # pylint: disable=too-few-public-methods
    def __init__(self, time: float, callback: Callable[[], None]):
        self.time = time
        self.callback = callback

    def __lt__(self, other):
        return self.time < other.time
