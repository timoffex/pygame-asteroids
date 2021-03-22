import itertools
import math

from typing import Any

from .aabb import AABB


class QuadtreeCollider:
    def __init__(self, aabb: AABB, data: Any):
        self._aabb = aabb
        self.data = data

    @property
    def aabb(self) -> AABB:
        return self._aabb


class _QuadtreeNode:
    def __init__(self, aabb: AABB, depth: int = 0, max_depth: int = 10):
        self._children = None
        self._colliders = []
        self._max_load = 5
        self._aabb = aabb
        self._depth = depth
        self._max_depth = max_depth

    def make_subtrees(self):
        x_mid = 0.5 * (self._aabb.x_max + self._aabb.x_min)
        y_mid = 0.5 * (self._aabb.y_max + self._aabb.y_min)
        new_depth = self._depth + 1

        return [
            _QuadtreeNode(
                AABB(
                    x_min=x_mid,
                    x_max=self._aabb.x_max,
                    y_min=y_mid,
                    y_max=self._aabb.y_max,
                ),
                depth=new_depth,
                max_depth=self._max_depth,
            ),
            _QuadtreeNode(
                AABB(
                    x_min=self._aabb.x_min,
                    x_max=x_mid,
                    y_min=y_mid,
                    y_max=self._aabb.y_max,
                ),
                depth=new_depth,
                max_depth=self._max_depth,
            ),
            _QuadtreeNode(
                AABB(
                    x_min=self._aabb.x_min,
                    x_max=x_mid,
                    y_min=self._aabb.y_min,
                    y_max=y_mid,
                ),
                depth=new_depth,
                max_depth=self._max_depth,
            ),
            _QuadtreeNode(
                AABB(
                    x_min=x_mid,
                    x_max=self._aabb.x_max,
                    y_min=self._aabb.y_min,
                    y_max=y_mid,
                ),
                depth=new_depth,
                max_depth=self._max_depth,
            ),
        ]

    def intersects(self, collider: QuadtreeCollider):
        return collider.aabb.intersects(self._aabb)

    def add(self, collider: QuadtreeCollider):
        if self._children is None:
            self._add_to_self(collider)
        else:
            self._add_to_children(collider)

    def subdivide(self):
        assert self._children is None

        self._children = self.make_subtrees()
        for collider in self._colliders:
            for child in self._children:
                if child.intersects(collider):
                    child.add(collider)
        self._colliders = None

    def get_nearby_pairs(self):
        if self._children is not None:

            def order_pair(pair):
                if id(pair[0]) > id(pair[1]):
                    return (pair[1], pair[0])
                else:
                    return pair

            pairs = set()
            for child in self._children:
                pairs |= set(map(order_pair, child.get_nearby_pairs()))
            return pairs
        else:
            return filter(
                lambda pair: pair[0].aabb.intersects(pair[1].aabb),
                itertools.combinations(self._colliders, 2),
            )

    def get_debug_bounding_boxes(self) -> list[AABB]:
        if self._children is None:
            return [self._aabb]
        else:
            return [self._aabb] + [
                box
                for child in self._children
                for box in child.get_debug_bounding_boxes()
            ]

    def _add_to_self(self, collider: QuadtreeCollider):
        if (
            self._depth < self._max_depth
            and len(self._colliders) + 1 >= self._max_load
        ):
            self.subdivide()
            self._add_to_children(collider)
        else:
            self._colliders.append(collider)

    def _add_to_children(self, collider: QuadtreeCollider):
        for child in self._children:
            if child.intersects(collider):
                child.add(collider)


class Quadtree:
    def __init__(self, colliders: list[QuadtreeCollider]):
        x_min = math.inf
        x_max = -math.inf
        y_min = math.inf
        y_max = -math.inf

        assert len(colliders) > 0
        for collider in colliders:
            x_min = min(x_min, collider.aabb.x_min)
            x_max = max(x_max, collider.aabb.x_max)
            y_min = min(y_min, collider.aabb.y_min)
            y_max = max(y_max, collider.aabb.y_max)

        self._root = _QuadtreeNode(
            AABB(
                x_min=x_min,
                x_max=x_max,
                y_min=y_min,
                y_max=y_max,
            )
        )

        for collider in colliders:
            self._root.add(collider)

    def get_nearby_pairs(self) -> list[(QuadtreeCollider, QuadtreeCollider)]:
        return self._root.get_nearby_pairs()

    def get_debug_bounding_boxes(self) -> list[AABB]:
        return self._root.get_debug_bounding_boxes()
