import itertools

from game_object import GameObject
from transform import Transform
from typing import Any, Protocol


class Collision:
    """An immutable data type containing information about a collision
    between one physics body and another.

    """

    def __init__(self, *, body_self: "PhysicsBody", body_other: "PhysicsBody"):
        self.body_self = body_self
        self.body_other = body_other


class CollisionHook(Protocol):
    """Protocol for physics collision hooks."""

    def __call__(self, collision: Collision) -> None:
        ...


class PhysicsBody:
    """A physics object that has a velocity and may collide with other
    physics objects.

    This is the main object in the physics system. Use methods on
    PhysicsSystem to create new PhysicsBody instances.

    The physics system modifies the body's transform to move it
    according to its velocity.

    """

    def __init__(self, physics_system, *, mass: float, transform: Transform):
        self._system = physics_system
        self._collision_hooks: set[CollisionHook] = set()
        self._data = list()
        self.transform = transform
        self.velocity_x = 0
        self.velocity_y = 0
        self.mass = mass

    def disable(self):
        """Removes this physics body from the simulation."""
        self._system._objects.discard(self)

    def enable(self):
        """Adds this physics body to the simulation."""
        self._system._objects.add(self)

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


def add_physics_component(go: GameObject, body: PhysicsBody):
    go.add_destroy_hook(lambda: body.disable())


class _PhysicsCircleBody(PhysicsBody):
    """A physics body with a circle collider.

    Do not use this outside of the physics system.

    """

    def __init__(
        self,
        physics_system,
        *,
        mass: float,
        transform: Transform,
        radius: float
    ):
        super().__init__(physics_system, mass=mass, transform=transform)
        self._radius = radius

    def radius(self):
        return self._radius

    def overlaps(self, other):
        dx = self.transform.x() - other.transform.x()
        dy = self.transform.y() - other.transform.y()

        dist_squared = dx ** 2 + dy ** 2

        radii_sum = self.radius() + other.radius()
        radii_sum_squared = radii_sum * radii_sum

        return dist_squared < radii_sum_squared


class PhysicsSystem:
    """A system that implements velocities and collisions in a
    reality-inspired way.

    """

    def __init__(self):
        self._objects: set[PhysicsBody] = set()

    def new_circle_body(
        self, *, mass: float, transform: Transform, radius: float
    ) -> PhysicsBody:
        """Creates a new PhysicsBody with a circular collider centered at the
        transform.

        """
        body = _PhysicsCircleBody(
            self, transform=transform, radius=radius, mass=mass
        )
        self._objects.add(body)
        return body

    def update(self, delta_time: float):
        # Detect collisions
        # TODO: Construct a quadtree

        hooks = set()

        overlapping_pairs = filter(
            lambda pair: pair[0].overlaps(pair[1]),
            itertools.combinations(self._objects, 2),
        )
        for (obj1, obj2) in overlapping_pairs:
            # Compute collision impulse that is orthogonal to the
            # collision plane and conserves momentum and kinetic
            # energy

            # TODO: Allow non-elastic collisions (friction)
            # TODO: Implement angular momentum

            dx = obj1.transform.x() - obj2.transform.x()
            dy = obj1.transform.y() - obj2.transform.y()
            dist_squared = dx ** 2 + dy ** 2

            if dist_squared == 0:
                # give up, objects are perfectly overlapping so we
                # can't figure out a direction in which they should
                # bounce
                continue

            vx = obj1.velocity_x - obj2.velocity_x
            vy = obj1.velocity_y - obj2.velocity_y

            # The multiplier that ensures the bounce preserves kinetic
            # energy
            t = -(
                2
                * (vx * dx + vy * dy)
                / (1 / obj1.mass + 1 / obj2.mass)
                / dist_squared
            )

            if t < 0:
                # The objects were overlapping but moving away from
                # each other, so don't bounce them
                continue

            obj1.add_impulse((dx * t, dy * t))
            obj2.add_impulse((-dx * t, -dy * t))

            def map_hook(collision):
                def apply_hook(h):
                    def run():
                        h(collision=collision)

                    return run

                return apply_hook

            collision1 = Collision(body_self=obj1, body_other=obj2)
            hooks |= set(map(map_hook(collision1), obj1._collision_hooks))

            collision2 = Collision(body_self=obj2, body_other=obj1)
            hooks |= set(map(map_hook(collision2), obj2._collision_hooks))

        # Apply velocities
        for obj in self._objects:
            obj.transform.add_x(obj.velocity_x * delta_time)
            obj.transform.add_y(obj.velocity_y * delta_time)

        # Run hooks
        for hook in hooks:
            hook()

    def kinetic_energy(self) -> float:
        """Computes the total kinetic energy of all physics objects."""
        return sum(map(lambda obj: obj.kinetic_energy(), self._objects))

    def total_momentum(self) -> (float, float):
        """Computes the total momentum of all physics objects."""
        mx = 0
        my = 0
        for obj in self._objects:
            mx += obj.mass * obj.velocity_x
            my += obj.mass * obj.velocity_y
        return (mx, my)
