from abc import ABC, abstractmethod
from dataclasses import dataclass
import math
from typing import Any, Protocol

from game_objects import GameObject
from transform import Transform

from .collider import Collider


@dataclass(frozen=True)
class Collision:
    """An immutable data type containing information about a collision
    between one physics body and another.

    """

    body_self: "PhysicsBody"
    body_other: "PhysicsBody"


class CollisionHook(Protocol):
    """Protocol for physics collision hooks."""

    def __call__(self, collision: Collision) -> None:
        ...


class PhysicsBody(ABC):
    """A moving, colliding physical object.

    Physics bodies have a velocity and can collide with other physics
    objects depending on the attached colliders.

    This is an abstract class. Use methods on a PhysicsSystem to create
    physics bodies within it.

    The physics system modifies the body's transform to move it
    according to its velocity. Behavior is undefined if the body's
    transform has a parent transform. If you want to attach two physics
    bodies to each other, you're probably looking for a "physics joint",
    which are not implemented in this project.

    """

    def __init__(
        self,
        game_object: GameObject,
        mass: float,
        transform: Transform,
    ):
        self._game_object = game_object
        self._collision_hooks: set[CollisionHook] = set()
        self._data = list()
        self.transform = transform
        self.velocity_x = 0
        self.velocity_y = 0
        self.mass = mass

        self._remove_destroy_hook = self._game_object.on_destroy(self.destroy)
        self._is_destroyed = False
        self._colliders: set["RegularCollider"] = set()

    @property
    def speed(self):
        return math.sqrt(self.velocity_x ** 2 + self.velocity_y ** 2)

    def destroy(self):
        """Removes this physics body from the simulation."""
        if self._is_destroyed:
            return

        self._is_destroyed = True
        self._remove_destroy_hook()

        colliders = set(self._colliders)
        for collider in colliders:
            collider.destroy()

    def add_circle_collider(self, radius: float) -> "RegularCollider":
        """Adds a circular collision zone to this physics body.

        The collider is centered on the physics body's transform.

        """

        # NOTE: Before I allow non-centered colliders, I'll need to fix how the
        # physics system computes the collision impulse (right now it only
        # works for centered circles). I'll also need to implement rotational
        # physics and allow specifying how much of a body's mass is contained
        # in each collider (for computing the center of mass).

        collider = self._make_circle_collider(radius)
        self._colliders.add(collider)
        return collider

    @abstractmethod
    def _make_circle_collider(self, radius: float) -> "RegularCollider":
        pass

    def add_impulse(self, impulse: (float, float)):
        """Applies an impulse to the physics body.

        An impulse is a change in momentum. This adds to the physics
        body's velocity the result of dividing the impulse by the
        object's mass.

        """
        (ix, iy) = impulse

        self.velocity_x += ix / self.mass
        self.velocity_y += iy / self.mass

    def kinetic_energy(self):
        """Computes the kinetic energy of the physics body."""
        return 0.5 * self.mass * (self.velocity_x ** 2 + self.velocity_y ** 2)

    def add_collision_hook(self, hook: CollisionHook):
        """Registers a function that runs whenever this body collides with
        another.

        """
        self._collision_hooks.add(hook)

    def add_data(self, data: Any):
        """Adds data to the physics object.

        Data can be any object and order is preserved.

        """
        self._data.append(data)

    def get_data(self) -> list[Any]:
        """Returns a copy of the data associated to this physics object."""
        return list(self._data)


class RegularCollider(Collider):
    """A collider attached to a PhysicsBody.

    This is an abstract class. Create colliders of the desired shape by
    using methods on a PhysicsBody. The collider belongs to the PhysicsBody
    from which it was created.

    """

    @abstractmethod
    def __init__(self, physics_body: PhysicsBody):
        super().__init__()
        self._body = physics_body
        self._remove_destroy_hook = self._body._game_object.on_destroy(
            self.destroy
        )

    def destroy(self):
        self._body._colliders.discard(self)
        self._remove_destroy_hook()
        super().destroy()

    def get_data(self) -> list[Any]:
        return self.body.get_data()

    @property
    def body(self) -> PhysicsBody:
        return self._body

    @property
    def transform(self) -> Transform:
        return self.body.transform
