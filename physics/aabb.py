class AABB:
    """An immutable data type representing an axis-aligned bounding box."""

    def __init__(self, x_min: float, x_max: float, y_min: float, y_max: float):
        self._x_min = x_min
        self._x_max = x_max
        self._y_min = y_min
        self._y_max = y_max

    @property
    def x_min(self):
        self._x_min

    @property
    def x_max(self):
        self._x_max

    @property
    def y_min(self):
        self._y_min

    @property
    def y_max(self):
        self._y_max
