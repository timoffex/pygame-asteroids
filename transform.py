import math

from typing import Optional


class Transform:
    """A mutable object that represents a 2D translation and rotation."""

    def __init__(self, parent: Optional["Transform"] = None):
        self._x = 0
        self._y = 0
        self._angle = 0
        self._parent = parent

    def x(self):
        if self._parent:
            parent_angle = self._parent.angle()
            return (
                self._parent.x()
                + self._x * math.cos(parent_angle)
                + self._y * math.sin(parent_angle)
            )
        return self._x

    def add_x(self, dx):
        self._x += dx

    def set_local_x(self, x):
        self._x = x

    def y(self):
        if self._parent:
            parent_angle = self._parent.angle()
            return (
                self._parent.y()
                - self._x * math.sin(parent_angle)
                + self._y * math.cos(parent_angle)
            )
        return self._y

    def add_y(self, dy):
        self._y += dy

    def set_local_y(self, y):
        self._y = y

    def angle(self):
        if self._parent:
            return self._parent.angle() + self._angle
        return self._angle

    def rotate(self, radians):
        self._angle += radians

    def set_local_angle(self, radians):
        self._angle = radians
