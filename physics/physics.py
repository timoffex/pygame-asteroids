from dataclasses import dataclass
from game_object import GameObject
from transform import Transform
from typing import Any, Callable, Protocol

from .aabb import AABB
from .quadtree import Quadtree, QuadtreeCollider


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


class PhysicsBody:
    """A physics object that has a velocity and may collide with other
    physics objects.

    This is the main object in the physics system. Use methods on
    PhysicsSystem to create new PhysicsBody instances.

    The physics system modifies the body's transform to move it
    according to its velocity.

    """

    def __init__(
        self,
        physics_system,
        *,
        game_object: GameObject,
        mass: float,
        transform: Transform,
    ):
        self._system = physics_system
        self._system._bodies.add(self)

        self._game_object = game_object
        self._collision_hooks: set[CollisionHook] = set()
        self._data = list()
        self.transform = transform
        self.velocity_x = 0
        self.velocity_y = 0
        self.mass = mass

        self._game_object.add_destroy_hook(self.destroy)
        self._is_destroyed = False
        self._colliders: set["Collider"] = set()

    def destroy(self):
        """Removes this physics body from the simulation."""
        if self._is_destroyed:
            return

        self._is_destroyed = True
        self._system._bodies.discard(self)
        self._game_object.remove_destroy_hook(self.destroy)

        colliders = set(self._colliders)
        for collider in colliders:
            collider.destroy()

    def add_circle_collider(self, radius: float):
        collider = CircleCollider(
            radius=radius, physics_system=self._system, physics_body=self
        )
        self._colliders.add(collider)
        return collider

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


class Collider:
    """Abstract base class for collider objects.


    There are two types of colliders: regular colliders and trigger
    colliders.

    Regular colliders always belong to a PhysicsBody and should be
    created through the methods on PhysicsBody. Regular colliders cause
    their physics bodies to bounce off of each other when they collide.
    You can create an immovable collider by using a PhysicsBody with
    infinite mass.

    Trigger colliders do not belong to a PhysicsBody and are created
    through PhysicsSystem methods. Physics bodies do not bounce when
    they encounter trigger colliders. Trigger colliders are used to
    detect when something has entered an area on the screen.

    """

    def __init__(self, physics_system: "PhysicsSystem"):
        self._system = physics_system

    def destroy(self):
        pass

    def _make_aabb(self) -> AABB:
        raise NotImplementedError()


class RegularCollider(Collider):
    def __init__(
        self, physics_system: "PhysicsSystem", physics_body: PhysicsBody
    ):
        super().__init__(physics_system)
        self._body = physics_body

    def destroy(self):
        self._body._colliders.discard(self)
        super().destroy()

    @property
    def body(self):
        return self._body

    @property
    def transform(self):
        return self.body.transform


@dataclass(frozen=True)
class TriggerEvent:
    trigger_zone: "TriggerCollider"
    other_collider: Collider


class TriggerHook(Protocol):
    def __call__(self, trigger_event: TriggerEvent):
        ...


class TriggerCollider(Collider):
    def __init__(
        self,
        physics_system: "PhysicsSystem",
        transform: Transform,
        game_object: GameObject,
    ):
        super().__init__(physics_system)
        self._hooks: list[TriggerHook] = []
        self._transform = transform

        self._is_destroyed = False
        self._game_object = game_object
        self._game_object.add_destroy_hook(self.destroy)

    @property
    def transform(self):
        return self._transform

    def destroy(self):
        if not self._is_destroyed:
            self._game_object.remove_destroy_hook(self.destroy)
            self._is_destroyed = True
        super().destroy()

    def add_trigger_hook(self, hook: TriggerHook) -> Callable[[], None]:
        """Adds a hook that runs whenever something enters this collider.

        This returns a function that can be called to remove the added hook.

        """
        self._hooks.append(hook)
        did_remove = False

        def remove_hook():
            nonlocal did_remove
            if not did_remove:
                self._hooks.remove(hook)
                did_remove = True

        return remove_hook

    def _run_hooks(self, other_collider: Collider):
        event = TriggerEvent(trigger_zone=self, other_collider=other_collider)
        hooks = list(self._hooks)
        for hook in hooks:
            hook(event)


class _CircleColliderMixin:
    def __init__(self, radius: float, **kwargs):
        super().__init__(**kwargs)
        self._radius = radius

        self._system: PhysicsSystem
        self._system._circle_colliders.add(self)

    @property
    def radius(self):
        return self._radius

    def destroy(self):
        self._system._circle_colliders.remove(self)
        super().destroy()

    def _overlaps(self, other: "_CircleColliderMixin"):
        dx = self.transform.x() - other.transform.x()
        dy = self.transform.y() - other.transform.y()

        dist_squared = dx ** 2 + dy ** 2

        radii_sum = self.radius + other.radius
        radii_sum_squared = radii_sum * radii_sum

        return dist_squared < radii_sum_squared

    def _make_aabb(self) -> AABB:
        return AABB(
            x_min=self.transform.x() - self.radius,
            x_max=self.transform.x() + self.radius,
            y_min=self.transform.y() - self.radius,
            y_max=self.transform.y() + self.radius,
        )


class CircleCollider(_CircleColliderMixin, RegularCollider):
    pass


class CircleTriggerCollider(_CircleColliderMixin, TriggerCollider):
    pass


class PhysicsSystem:
    """A system that implements velocities and collisions in a
    reality-inspired way.

    """

    def __init__(self):
        self._bodies: set[PhysicsBody] = set()
        self._circle_colliders: set[_CircleColliderMixin] = set()
        self._debug_bounding_boxes = []
        self.debug_save_bounding_boxes = False

    def new_circle_body(
        self,
        *,
        radius: float,
        transform: Transform,
        game_object: GameObject,
        mass: float,
    ) -> PhysicsBody:
        """Creates a new PhysicsBody with a circular collider centered at the
        transform.

        """
        body = PhysicsBody(
            self, game_object=game_object, mass=mass, transform=transform
        )
        body.add_circle_collider(radius=radius)
        return body

    def new_circle_trigger(
        self, *, radius: float, transform: Transform, game_object: GameObject
    ) -> CircleTriggerCollider:
        return CircleTriggerCollider(
            physics_system=self,
            radius=radius,
            transform=transform,
            game_object=game_object,
        )

    def update(self, delta_time: float):
        # Detect collisions
        self._process_collisions()

        # Apply velocities
        for obj in self._bodies:
            obj.transform.add_x(obj.velocity_x * delta_time)
            obj.transform.add_y(obj.velocity_y * delta_time)

    def kinetic_energy(self) -> float:
        """Computes the total kinetic energy of all physics objects."""
        return sum(map(lambda obj: obj.kinetic_energy(), self._bodies))

    def total_momentum(self) -> (float, float):
        """Computes the total momentum of all physics objects."""
        mx = 0
        my = 0
        for obj in self._bodies:
            mx += obj.mass * obj.velocity_x
            my += obj.mass * obj.velocity_y
        return (mx, my)

    def get_overlapping_pairs(self) -> list[(PhysicsBody, PhysicsBody)]:
        quadtree = Quadtree(
            list(
                map(
                    lambda circle: QuadtreeCollider(
                        aabb=circle._make_aabb(), data=circle
                    ),
                    self._circle_colliders,
                )
            )
        )

        if self.debug_save_bounding_boxes:
            self._debug_bounding_boxes = quadtree.get_debug_bounding_boxes()

        return map(
            lambda pair: (pair[0].data, pair[1].data),
            filter(
                lambda pair: pair[0].data._overlaps(pair[1].data),
                quadtree.get_nearby_pairs(),
            ),
        )

    def debug_get_bounding_boxes(self) -> list[AABB]:
        return self._debug_bounding_boxes

    def _process_collisions(self):
        for (obj1, obj2) in self.get_overlapping_pairs():
            # Compute collision impulse that is orthogonal to the
            # collision plane and conserves momentum and kinetic
            # energy

            # TODO: Allow non-elastic collisions (friction)
            # TODO: Implement angular momentum

            if isinstance(obj1, TriggerCollider):
                obj1._run_hooks(obj2)

            if isinstance(obj2, TriggerCollider):
                obj2._run_hooks(obj1)

            if isinstance(obj1, RegularCollider) and isinstance(
                obj2, RegularCollider
            ):
                dx = obj1.transform.x() - obj2.transform.x()
                dy = obj1.transform.y() - obj2.transform.y()
                dist_squared = dx ** 2 + dy ** 2

                if dist_squared == 0:
                    # give up, objects are perfectly overlapping so we
                    # can't figure out a direction in which they should
                    # bounce
                    continue

                body1 = obj1.body
                body2 = obj2.body

                vx = body1.velocity_x - body2.velocity_x
                vy = body1.velocity_y - body2.velocity_y

                v_dot_d = vx * dx + vy * dy
                if v_dot_d > 0:
                    # The objects were overlapping but moving away from
                    # each other, so don't bounce them
                    continue

                mass_divisor = 1 / body1.mass + 1 / body2.mass

                if mass_divisor > 0:
                    # The multiplier that ensures the bounce preserves kinetic
                    # energy
                    t = -(2 * v_dot_d / mass_divisor / dist_squared)

                    body1.add_impulse((dx * t, dy * t))
                    body2.add_impulse((-dx * t, -dy * t))

                collision1 = Collision(body_self=body1, body_other=body2)
                for hook in body1._collision_hooks:
                    hook(collision=collision1)

                collision2 = Collision(body_self=body2, body_other=body1)
                for hook in body2._collision_hooks:
                    hook(collision=collision2)
