class Transform:
    """A mutable object that represents a 2D translation and rotation."""

    def __init__(self):
        self._x = 0
        self._y = 0
        self._angle = 0

    def x(self):
        return self._x

    def add_x(self, dx):
        self._x += dx

    def set_local_x(self, x):
        self._x = x

    def y(self):
        return self._y

    def add_y(self, dy):
        self._y += dy

    def set_local_y(self, y):
        self._y = y

    def angle(self):
        return self._angle

    def rotate(self, radians):
        self._angle += radians

    def set_local_angle(self, radians):
        self._angle = radians
