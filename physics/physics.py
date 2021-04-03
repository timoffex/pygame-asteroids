from game_object import GameObject
from transform import Transform
from typing import Tuple

from .aabb import AABB
from .quadtree import Quadtree, QuadtreeCollider
from .collider import Collider
from .physics_body import Collision, PhysicsBody, RegularCollider
from .triggers import TriggerCollider, TriggerEvent


class PhysicsSystem:
    """An object that implements physics.

    A physics system consists of trigger zones and physics bodies that
    can have colliders. The system detects collisions, moves physics
    bodies and runs trigger zone hooks whenever update() is called.

    """

    def __init__(self):
        self._bodies: set[_PhysicsBody] = set()
        self._circle_colliders: set[_CircleColliderMixin] = set()
        self._triggers: set[_TriggerCollider] = set()

        self._debug_bounding_boxes = []
        self.debug_save_bounding_boxes = False

    def new_body(
        self,
        *,
        game_object: GameObject,
        transform: Transform,
        mass: float,
    ) -> PhysicsBody:
        return _PhysicsBody(
            physics_system=self,
            game_object=game_object,
            transform=transform,
            mass=mass,
        )

    def new_circle_trigger(
        self, *, radius: float, transform: Transform, game_object: GameObject
    ) -> TriggerCollider:
        """Creates a circular trigger zone.

        The circle is centered on the given transform.

        """

        return _CircleTriggerCollider(
            physics_system=self,
            radius=radius,
            transform=transform,
            game_object=game_object,
        )

    def update(self, delta_time: float):
        # Detect collisions
        self._detect_and_process_collisions()

        # Run triggers
        self._run_triggers()

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

    def _run_triggers(self):
        triggers = list(self._triggers)
        for trigger in triggers:
            trigger.run_triggers()

    def _detect_and_process_collisions(self):
        collisions: set[Tuple[PhysicsBody, PhysicsBody]] = set()

        def record_collision(obj1: PhysicsBody, obj2: PhysicsBody):
            collisions.add(
                (obj1, obj2) if id(obj1) < id(obj2) else (obj2, obj1)
            )

        for (obj1, obj2) in self.get_overlapping_pairs():
            # Compute collision impulse that is orthogonal to the
            # collision plane and conserves momentum and kinetic
            # energy

            # TODO: Allow non-elastic collisions (friction)
            # TODO: Implement angular momentum

            if isinstance(obj1, _TriggerCollider):
                obj1.add_current_collider(obj2)

            if isinstance(obj2, _TriggerCollider):
                obj2.add_current_collider(obj1)

            if isinstance(obj1, _RegularCollider) and isinstance(
                obj2, _RegularCollider
            ):
                record_collision(obj1.body, obj2.body)

        for (body1, body2) in collisions:
            self._process_collision_between(body1, body2)

    def _process_collision_between(
        self, body1: PhysicsBody, body2: PhysicsBody
    ):
        # TODO: Collisions only correct for centered circles
        dx = body1.transform.x - body2.transform.x
        dy = body1.transform.y - body2.transform.y
        dist_squared = dx ** 2 + dy ** 2

        if dist_squared == 0:
            # give up, objects are perfectly overlapping so we
            # can't figure out a direction in which they should
            # bounce
            return

        vx = body1.velocity_x - body2.velocity_x
        vy = body1.velocity_y - body2.velocity_y

        v_dot_d = vx * dx + vy * dy
        if v_dot_d > 0:
            # The objects were overlapping but moving away from
            # each other, so don't bounce them
            return

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


class _TriggerCollider(TriggerCollider):
    def __init__(
        self,
        physics_system: PhysicsSystem,
        transform: Transform,
        game_object: GameObject,
    ):
        super().__init__(transform=transform, game_object=game_object)

        self._system = physics_system
        self._system._triggers.add(self)

        self._previous_colliders: set[Collider] = set()
        self._new_colliders: set[Collider] = set()

    def destroy(self):
        self._system._triggers.discard(self)
        super().destroy()

    def run_triggers(self):
        exited = self._previous_colliders - self._new_colliders
        entered = self._new_colliders - self._previous_colliders
        stayed = self._previous_colliders & self._new_colliders

        for collider in exited:
            event = TriggerEvent(trigger_zone=self, other_collider=collider)
            for hook in self._exit_hooks:
                hook(event)

        for collider in entered:
            event = TriggerEvent(trigger_zone=self, other_collider=collider)
            for hook in self._enter_hooks:
                hook(event)

        for collider in stayed:
            event = TriggerEvent(trigger_zone=self, other_collider=collider)
            for hook in self._stay_hooks:
                hook(event)

        self._previous_colliders = self._new_colliders
        self._new_colliders = set()

    def add_current_collider(self, collider: Collider):
        self._new_colliders.add(collider)


class _RegularCollider(RegularCollider):
    def __init__(self, physics_system: PhysicsSystem, **kwargs):
        super().__init__(**kwargs)


class _CircleColliderMixin(Collider):
    def __init__(self, physics_system: PhysicsSystem, radius: float, **kwargs):
        super().__init__(physics_system=physics_system, **kwargs)
        self._radius = radius

        self._system = physics_system
        self._system._circle_colliders.add(self)

    @property
    def radius(self):
        return self._radius

    def destroy(self):
        self._system._circle_colliders.discard(self)
        super().destroy()

    def _overlaps(self, other: "_CircleColliderMixin"):
        dx = self.transform.x - other.transform.x
        dy = self.transform.y - other.transform.y

        dist_squared = dx ** 2 + dy ** 2

        radii_sum = self.radius + other.radius
        radii_sum_squared = radii_sum * radii_sum

        return dist_squared < radii_sum_squared

    def _make_aabb(self) -> AABB:
        return AABB(
            x_min=self.transform.x - self.radius,
            x_max=self.transform.x + self.radius,
            y_min=self.transform.y - self.radius,
            y_max=self.transform.y + self.radius,
        )


class _CircleCollider(_CircleColliderMixin, _RegularCollider):
    pass


class _CircleTriggerCollider(_CircleColliderMixin, _TriggerCollider):
    pass


class _PhysicsBody(PhysicsBody):
    def __init__(
        self,
        physics_system: PhysicsSystem,
        game_object: GameObject,
        transform: Transform,
        mass: float,
    ):
        super().__init__(
            game_object=game_object,
            transform=transform,
            mass=mass,
        )

        self._system = physics_system
        self._system._bodies.add(self)

    def destroy(self):
        self._system._bodies.discard(self)

    def _make_circle_collider(self, radius: float) -> RegularCollider:
        return _CircleCollider(
            physics_body=self, physics_system=self._system, radius=radius
        )
