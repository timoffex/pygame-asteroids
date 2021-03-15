from transform import Transform


class PhysicsBody:
    def __init__(self, physics_system, transform: Transform):
        self._system = physics_system
        self._transform = transform
        self.velocity_x = 0
        self.velocity_y = 0

    def disable(self):
        """Removes this physics body from the simulation."""
        self.physics_system._objects.remove(self)

    def enable(self):
        """Adds this physics body to the simulation."""
        self.physics_system._objects.add(self)


class PhysicsCircleBody(PhysicsBody):
    def __init__(self, physics_system, transform: Transform, radius: float):
        super().__init__(physics_system, transform)
        self._radius = radius

    def radius(self):
        return self._radius


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
        for obj in self._objects:
            obj._transform.add_x(obj.velocity_x * delta_time)
            obj._transform.add_y(obj.velocity_y * delta_time)
