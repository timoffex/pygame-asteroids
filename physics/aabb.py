class AABB:
    """An immutable data type representing an axis-aligned bounding box."""

    def __init__(self, x_min: float, x_max: float, y_min: float, y_max: float):
        self._x_min = x_min
        self._x_max = x_max
        self._y_min = y_min
        self._y_max = y_max

    @property
    def x_min(self):
        return self._x_min

    @property
    def x_max(self):
        return self._x_max

    @property
    def y_min(self):
        return self._y_min

    @property
    def y_max(self):
        return self._y_max

    @property
    def width(self):
        return self.x_max - self.x_min

    @property
    def height(self):
        return self.y_max - self.y_min

    def intersects(self, other: "AABB") -> bool:
        return (
            self.x_max >= other.x_min
            and self.x_min <= other.x_max
            and self.y_max >= other.y_min
            and self.y_min <= other.y_max
        )

    def __str__(self):
        return (
            f"AABB(({self.x_min}, {self.y_min})"
            + f" to ({self.x_max}, {self.y_max}))"
        )
