from transform import Transform


class PhysicsBody:
    def __init__(self, physics_system, *,
                 mass: float, transform: Transform):
        self._system = physics_system
        self.transform = transform
        self.velocity_x = 0
        self.velocity_y = 0
        self.mass = mass

    def disable(self):
        """Removes this physics body from the simulation."""
        self.physics_system._objects.remove(self)

    def enable(self):
        """Adds this physics body to the simulation."""
        self.physics_system._objects.add(self)

    def add_impulse(self, impulse):
        (ix, iy) = impulse

        self.velocity_x += ix / self.mass
        self.velocity_y += iy / self.mass

    def kinetic_energy(self):
        return 0.5 * self.mass * (self.velocity_x ** 2 + self.velocity_y ** 2)


class PhysicsCircleBody(PhysicsBody):
    def __init__(self, physics_system, *,
                 mass: float,
                 transform: Transform,
                 radius: float):
        super().__init__(physics_system,
                         mass=mass,
                         transform=transform)
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
    def __init__(self):
        self._objects = set()

    def new_circle_body(self, *,
                        mass: float,
                        transform: Transform,
                        radius: float) -> PhysicsBody:
        body = PhysicsCircleBody(self,
                                 transform=transform,
                                 radius=radius,
                                 mass=mass)
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
                    dx = obj1.transform.x() - obj2.transform.x()
                    dy = obj1.transform.y() - obj2.transform.y()
                    dist_squared = dx ** 2 + dy ** 2

                    if dist_squared == 0:
                        # give up, nothing to do
                        continue

                    vx = obj1.velocity_x - obj2.velocity_x
                    vy = obj1.velocity_y - obj2.velocity_y

                    t = -(2 * (vx * dx + vy * dy)
                          / (1/obj1.mass + 1/obj2.mass)
                          / dist_squared)

                    if t < 0:
                        # The objects were moving away from each other
                        continue

                    obj1.add_impulse((dx * t, dy * t))
                    obj2.add_impulse((-dx * t, -dy * t))

        # Apply velocities
        for obj in self._objects:
            obj.transform.add_x(obj.velocity_x * delta_time)
            obj.transform.add_y(obj.velocity_y * delta_time)

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
