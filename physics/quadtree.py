import itertools

from typing import Any

from .aabb import AABB


class QuadtreeCollider:
    def __init__(self, aabb: AABB, data: Any):
        self._aabb = aabb
        self.data = data

    @property
    def aabb(self):
        self._aabb


class Quadtree:
    def __init__(self):
        self._colliders: list[QuadtreeCollider] = []

    def add(self, collider: QuadtreeCollider):
        self._colliders.append(collider)

    def remove(self, collider: QuadtreeCollider):
        self._colliders.remove(collider)

    def get_nearby_pairs(self) -> list[(QuadtreeCollider, QuadtreeCollider)]:
        return itertools.combinations(self._colliders, 2)
