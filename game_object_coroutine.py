from game_objects import GameObject
from game_time import GameTime
from typing import Callable, Generator, Optional

GameCoroutineGenerator = Generator[
    Optional["GameYieldInstruction"], float, None
]
"""A Generator that can be used to create a `GameObjectCoroutine`.

GameObjectCoroutine generators yield either `None` or
`GameYieldInstruction`. Yielding `None` causes the coroutine to wait
until the next `GameObject` update loop. More complex behaviors can be
created by yielding an object of type `GameYieldInstruction`.

Use the `yield from` statement to run another `GameCoroutineGenerator`
as part of your coroutine.

"""


class GameObjectCoroutine:
    """A task associated to a `GameObject` that does work during update.

    `GameObjectCoroutine`s allow using a Python generator object to
    define work that gets done over multiple update iterations.

    A `GameObjectCoroutine` is attached to a specific `GameObject` and
    is executed on every update loop. GameObjectCoroutines can be
    suspended and resumed using the `suspend` and `start` methods;
    suspending a GameObjectCoroutine causes it to no longer run on the
    update loop until it is resumed.

    Since GameObjectCoroutines are attached to GameObjects, they stop
    running when their GameObject is destroyed.

    """

    def __init__(
        self, game_object: GameObject, coroutine: GameCoroutineGenerator
    ):
        """Creates a suspended `GameObjectCoroutine` attached to the
        `game_object`.

        """
        self._game_object = game_object
        self._coroutine = coroutine
        self._is_suspended = True
        self._is_yielding = False
        self._is_done = False
        self._did_start_once = False

        self._remove_update_hook = None

    def start(self):
        """Starts or resumes this coroutine.

        If this is starting the coroutine for the first time, it will
        run all the code up to the first yield statement.

        """
        if self._is_suspended and not self._is_yielding:
            self._remove_update_hook = self._game_object.on_update(
                self._update_hook
            )
            self._is_suspended = False

            if not self._did_start_once:
                self._run_and_process_yield(lambda: next(self._coroutine))
                self._did_start_once = True

    def suspend(self):
        """Pauses the coroutine so that it no longer runs when its `GameObject`
        updates.

        """
        if not self._is_suspended:
            self._remove_update_hook()
            self._is_suspended = True

    def is_done(self):
        """Returns whether this coroutine's generator finished running."""
        return self._is_done

    def _update_hook(self, delta_time: float):
        if self.is_done():
            self.suspend()
            return

        self._run_and_process_yield(lambda: self._coroutine.send(delta_time))

    def _run_and_process_yield(self, step_coroutine):
        try:
            yield_instruction = step_coroutine()

            if yield_instruction is not None:
                yield_instruction.apply(
                    game_object=self._game_object, coroutine=self
                )
        except StopIteration:
            self._is_done = True
        except Exception:
            self._is_done = True
            raise

    def _yield_control(self):
        self._remove_update_hook()
        self._is_yielding = True

    def _resume_control(self):
        if not self._is_suspended:
            self._remove_update_hook = self._game_object.on_update(
                self._update_hook
            )
        self._is_yielding = False


class GameYieldInstruction:
    """Base class for yield instructions that can be returned from a
    `GameCoroutineGenerator`.

    In a generator for a GameObjectCoroutine, you can `yield None` to
    wait until the next update loop. You can yield a
    `GameYieldInstruction` to implement more complex behaviors.

    This class is not meant to be subclassed outside of this library.

    """

    def apply(self, game_object: GameObject, coroutine: GameObjectCoroutine):
        ...


def resume_after(time: GameTime, delay_ms: float) -> GameYieldInstruction:
    """Returns a GameYieldInstruction that stops the coroutine from
    updating until a certain amount of time has passed.

    """

    def continuation(resume):
        time.run_after_delay(delay_ms=delay_ms, callback=resume)

    return resume_later(continuation)


def resume_later(
    continuation: Callable[[Callable[[], None]], None]
) -> GameYieldInstruction:
    """Returns a GameYieldInstruction that stops the coroutine from
    updating and allows custom code to resume it later.

    Example:
        # A hypothetical "time" object that schedules a continuation to run
        # at some later time.
        yield resume_later(lambda resume: time.after_delay(1000).run(resume))

    """
    return _ResumeLater(continuation)


class _ResumeLater(GameYieldInstruction):
    def __init__(self, resume: Callable[[Callable[[], None]], None]):
        self._resume = resume

    def apply(self, game_object: GameObject, coroutine: GameObjectCoroutine):
        coroutine._yield_control()

        did_resume = False

        def do_resume():
            nonlocal did_resume
            if not did_resume:
                coroutine._resume_control()
                did_resume = True

        self._resume(do_resume)
