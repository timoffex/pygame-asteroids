import heapq
import pygame

from typing import Callable


class GameTime:
    """An object that allows scheduling callbacks to run after delays."""
    def __init__(self):
        self._sorted_scheduled_events: list['_ScheduledEvent'] = []

    def run_after_delay(self,
                        delay_ms: float,
                        callback: Callable[[], None]):
        """Schedules a callback to run after the specified delay."""
        heapq.heappush(
            self._sorted_scheduled_events,
            _ScheduledEvent(
                time=pygame.time.get_ticks() + delay_ms,
                callback=callback))

    def run_callbacks(self):
        """Runs all callbacks whose time has come."""
        while len(self._sorted_scheduled_events) > 0:
            event = heapq.heappop(self._sorted_scheduled_events)
            if pygame.time.get_ticks() >= event.time:
                event.callback()
            else:
                # Add the event back
                heapq.heappush(self._sorted_scheduled_events, event)
                break


class _ScheduledEvent:
    def __init__(self, time: float, callback: Callable[[], None]):
        self.time = time
        self.callback = callback

    def __lt__(self, other):
        return self.time < other.time
