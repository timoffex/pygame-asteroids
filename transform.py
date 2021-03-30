"""Defines the Transform type."""

import math

from typing import Optional


class Transform:
    """A mutable object that represents a 2D translation and rotation."""

    def __init__(self, parent: Optional["Transform"] = None):
        self._x = 0
        self._y = 0
        self._angle = 0
        self._parent = parent

    @property
    def x(self):
        """This transform's global X translation."""
        if self._parent:
            parent_angle = self._parent.angle
            return (
                self._parent.x
                + self._x * math.cos(parent_angle)
                + self._y * math.sin(parent_angle)
            )
        return self._x

    def add_x(self, dx):
        """Adds to this transform's X translation."""
        self._x += dx

    def set_local_x(self, x):
        """Sets this transform's X translation relative to its parent."""
        self._x = x

    @property
    def y(self):
        """This transform's global Y translation."""
        if self._parent:
            parent_angle = self._parent.angle
            return (
                self._parent.y
                - self._x * math.sin(parent_angle)
                + self._y * math.cos(parent_angle)
            )
        return self._y

    def add_y(self, dy):
        """Adds to this transform's Y translation."""
        self._y += dy

    def set_local_y(self, y):
        """Sets this transform's Y translation relative to its parent."""
        self._y = y

    @property
    def angle(self):
        """This transform's global counterclockwise rotation in radians."""
        if self._parent:
            return self._parent.angle + self._angle
        return self._angle

    def rotate(self, radians):
        """Rotates this transform counterclockwise."""
        self._angle += radians

    def set_local_angle(self, radians):
        """Sets this transform's counterclockwise rotation relative to its
        parent.

        """
        self._angle = radians
