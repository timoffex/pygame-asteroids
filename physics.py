import math

from transform import Transform


class PhysicsBody:
    def __init__(self, physics_system, transform: Transform):
        self._system = physics_system
        self.transform = transform
        self.velocity_x = 0
        self.velocity_y = 0

    def disable(self):
        """Removes this physics body from the simulation."""
        self.physics_system._objects.remove(self)

    def enable(self):
        """Adds this physics body to the simulation."""
        self.physics_system._objects.add(self)

    def add_impulse(self, impulse):
        (ix, iy) = impulse

        # TODO: Use mass in calculation
        self.velocity_x += ix
        self.velocity_y += iy


class PhysicsCircleBody(PhysicsBody):
    def __init__(self, physics_system, transform: Transform, radius: float):
        super().__init__(physics_system, transform)
        self._radius = radius

    def radius(self):
        return self._radius

    def overlaps(self, other):
        dx = self.transform.x() - other.transform.x()
        dy = self.transform.y() - other.transform.y()

        dist_squared = dx * dx + dy * dy

        radii_sum = self.radius() + other.radius()
        radii_sum_squared = radii_sum * radii_sum

        return dist_squared < radii_sum_squared


class PhysicsSystem:
    def __init__(self):
        self._objects = set()

    def new_circle_body(self,
                        transform: Transform,
                        radius: float) -> PhysicsBody:
        body = PhysicsCircleBody(self, transform, radius)
        self._objects.add(body)
        return body

    def update(self, delta_time: float):
        # Detect collisions
        # TODO: Construct a quadtree
        remaining_objects = set(self._objects)
        for obj1 in self._objects:
            remaining_objects.remove(obj1)
            for obj2 in remaining_objects:
                if obj1.overlaps(obj2):
                    dx = obj2.transform.x() - obj1.transform.x()
                    dy = obj2.transform.y() - obj1.transform.y()
                    dist = math.sqrt(dx * dx + dy * dy)

                    if dist == 0:
                        # give up, nothing to do
                        continue

                    dx = dx / dist
                    dy = dy / dist

                    vx = obj2.velocity_x - obj1.velocity_x
                    vy = obj2.velocity_y - obj1.velocity_y

                    # TODO: Divide by sum of masses
                    t = 2 * (vx * dx + vy * dy)

                    if t > 0:
                        # The objects were moving away from each other
                        continue

                    obj1.add_impulse((dx * t, dy * t))
                    obj2.add_impulse((-dx * t, -dy * t))

        for obj in self._objects:
            obj.transform.add_x(obj.velocity_x * delta_time)
            obj.transform.add_y(obj.velocity_y * delta_time)
